import asyncio
import logging
import re
import time
from abc import ABC
from abc import abstractmethod
from asyncio import InvalidStateError
from typing import Optional
from typing import override

import asyncssh
import telnetlib3
from formica.models.constant import ConnectionType
from formica.models.constant import DEFAULT_CONNECT_TIMEOUT
from formica.models.constant import DEFAULT_IDLE_TIMEOUT
from formica.models.constant import DeviceType
from formica.models.models import CredentialModel
from formica.models.models import DeviceModel
from telnetlib3 import TelnetReader
from telnetlib3 import TelnetWriter


logger = logging.getLogger(__file__)


def _expect(text: str, patterns: list[str]) -> tuple[bool, str]:
    """True if any of the patterns is found in the text"""
    for pattern in patterns:
        if re.search(pattern, text):
            return True, pattern

    return False, ""


class BaseConnection(ABC):
    def __init__(
        self,
        host: str,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
        prompt: Optional[str] = "",
    ):
        self.host: str = host
        self._idle_timeout = idle_timeout
        self.running_command: Optional[str] = None
        self.prompt: str = prompt
        self._stdout_future: Optional[asyncio.Future[str]] = None
        self._last_active: float = time.time()
        self.current_command_timeout: Optional[float] = None

    def idle_timed_out(self) -> bool:
        """Is this connection idle for too long?"""
        if self.running_command is not None:
            return False

        return time.time() - self._last_active > self._idle_timeout

    @abstractmethod
    async def run_command(
        self, command: str, expect_prompt: Optional[str], timeout: float
    ) -> str:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class SSHConnection(BaseConnection):
    """Don't create this class directly using the constructor, use ConnectionFactory instead"""

    default_expect_prompts = [r">", r"#", r"assword"]

    def __init__(
        self,
        connection: asyncssh.SSHClientConnection,
        process: Optional[asyncssh.SSHClientProcess],
        device_type: DeviceType,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._connection = connection
        self._process = process
        self._device_type = device_type

    @classmethod
    async def expect_response(
        cls, process: asyncssh.SSHClientProcess, patterns, timeout=5
    ) -> Optional[str]:
        """Read the output for some time, return the output if any pattern is matched"""
        buffer = ""
        try:
            async with asyncio.timeout(timeout):
                while True:
                    chunk = await process.stdout.read(1024)
                    if len(chunk) != 0:
                        # print("chunk:", chunk.encode())
                        buffer += chunk
                        # print(f"Buffer: {buffer.encode()}")  # Debug log

                        for pattern in patterns:
                            if re.search(pattern, buffer):
                                print(f"Matched pattern: {pattern}")
                                return buffer

                        if "ENTER" in buffer:
                            buffer = buffer.rsplit("\n", 1)[0]

                            process.stdin.write("\n")
                            await process.stdin.drain()
                    else:
                        # No more data to read, break the loop
                        print("No more data to read from stdout")
                        break
        except asyncio.TimeoutError:
            pass
        return buffer

    @override
    async def run_command(
        self, command: str, expect_prompt: Optional[str], timeout: float
    ) -> str:
        """
        Schedule a command to run on this connection

        Args:
            command: The command to run on this connection
            expect_prompt: The expected prompt to wait for after command output
            timeout: Timeout for executing command

        Raises:
            InvalidStateError: When a command is already running
            ValueError: If no credentials found or if connection type not supported
        """
        if self.running_command is not None:
            raise InvalidStateError(
                f"A command is already running: {self.running_command}"
            )

        print(f"Run command: {command}")

        # Get Future for stdout
        if self._device_type == DeviceType.LINUX:
            self._stdout_future = asyncio.create_task(self._connection.run(command))
        elif self._device_type == DeviceType.GCOM:
            self._process.stdin.write(f"{command}\n")
            await self._process.stdin.drain()
            print(
                f"expect prompt is: {self.prompt if expect_prompt is None else expect_prompt}"
            )
            self._stdout_future = asyncio.create_task(
                SSHConnection.expect_response(
                    self._process,
                    [self.prompt if expect_prompt is None else expect_prompt],
                )
            )
        else:
            self._process.stdin.write(f"{command}\n")
            await self._process.stdin.drain()
            print(
                f"expect prompt is: {self.prompt if expect_prompt is None else expect_prompt}"
            )
            self._stdout_future = asyncio.create_task(
                SSHConnection.expect_response(
                    self._process,
                    [self.prompt if expect_prompt is None else expect_prompt],
                    timeout=5,
                )
            )

        self.running_command = command
        self._last_active = time.time()

        try:
            await self._stdout_future
            return self._get_output()
        except Exception as e:
            raise e
        except asyncio.TimeoutError as e:
            raise TimeoutError(
                f"Timeout when running command {command} on {self.host}: {e}"
            )

    def _get_output(self) -> str:
        """
        Get the result of the running command

        Returns:
            Tuple contains the command, and result of that command, or None, plus host at the end

        Raises:
            InvalidStateError: When no command is running
        """
        # Check if the task is done, else return False and empty string
        if self.running_command is None:
            raise InvalidStateError("No running command")

        if e := self._stdout_future.exception() is not None:
            raise ConnectionError(
                f"Exception when running command {self.running_command}: {e}"
            )

        if self._device_type == DeviceType.LINUX:
            result = self._stdout_future.result().stdout
            print("result is", result)
        else:
            result = self._stdout_future.result()
            logger.info(f"result running command {self.running_command} is: {result}")

        self._stdout_future = None
        self.running_command = None
        self.current_command_timeout = None

        return result

    @override
    async def close(self) -> None:
        self.running_command = None
        self._stdout_future = None
        self.current_command_timeout = None
        self._connection.close()
        await self._connection.wait_closed()


class TelnetConnection(BaseConnection):
    default_expect_usernames = [r"sername", r"ogin", r"ser name"]
    default_expect_passwords = [r"assword"]
    default_expect_prompts = [r">", r"#"]
    default_expect_errors = [r"error", r"Error"]
    """Don't create this class directly using the constructor, use ConnectionFactory instead"""

    def __init__(
        self,
        reader: TelnetReader,
        writer: TelnetWriter,
        device_type: DeviceType,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._reader: TelnetReader = reader
        self._writer: TelnetWriter = writer
        self._device_type = device_type

    # @classmethod
    # async def open_connection(cls, ip, port) -> tuple[TelnetReader, TelnetWriter]:
    #     error_string = ""
    #     for try_number in range(TELNET_MAX_RETRIES):
    #         try:
    #             print(
    #                 f"Try to connect to {ip} using telnet, port: {port}"
    #             )
    #             reader, writer = await telnetlib3.open_connection(ip, port, encoding="latin-1")
    #             return reader, writer
    #         except Exception as e:
    #             error_string += f"\n- {e}"
    #             print(f"Error connecting to {ip} using telnet (try number {try_number}): {str(e)}")
    #
    #     raise ConnectionError(f"Failed to connect to {ip} using telnet: {error_string}")

    @classmethod
    async def expect_response(
        cls, reader: TelnetReader, patterns, timeout=10
    ) -> tuple[str, str]:
        """Wait for any pattern from the list, checking received data in chunks."""
        buffer = ""
        try:
            while True:
                chunk = await asyncio.wait_for(
                    reader.read(1024), timeout=timeout
                )  # Read in chunks
                # print(f"Type of chunk: {type(chunk)}")
                # print(f"chunk: {chunk.encode()}")
                buffer += chunk
                # print(f"Type of buffer: {type(buffer)}")
                # print(f"Buffer: {buffer.encode()}")  # Debug log

                for pattern in patterns:
                    if re.search(pattern, buffer):
                        print(f"Matched pattern: {pattern}")
                        return buffer, pattern
        except asyncio.TimeoutError:
            print("Timeout while waiting for response")
            return buffer, ""

    @classmethod
    async def expect_response2(
        cls, reader: TelnetReader, patterns: list[str]
    ) -> Optional[str]:
        """Wait for a specific pattern in the response"""
        found = False
        while not found:
            response = await reader.readuntil(b"\n")  # Read a line
            print(f"response to expect {patterns} from:")
            print(response)

            decoded_response = response.decode("utf-8").strip()

            for pattern in patterns:
                if re.search(pattern, decoded_response):
                    return decoded_response
        return None

    @classmethod
    async def send_command(cls, writer: TelnetWriter, command: str) -> None:
        writer.write(command + "\n")
        await writer.drain()

    async def run_command(
        self, command: str, expect_prompt: Optional[str], timeout: float
    ) -> str:
        """
        Schedule a command to run on this connection

        Args:
            command: The command to run on this connection
            expect_prompt: The expected prompt to wait for after command output
            timeout: Timeout for executing command

        Raises:
            InvalidStateError: When a command is already running
            ValueError: If no credentials found or if connection type not supported
        """
        if self.running_command is not None:
            raise InvalidStateError(
                f"A command is already running: {self.running_command}"
            )

        print(f"Run command: {command}")

        self._stdout_future = asyncio.create_task(
            asyncio.wait_for(
                self._schedule_run_command(command, expect_prompt), timeout=timeout
            )
        )
        self.running_command = command
        self.current_command_timeout = timeout
        self._last_active = time.time()

        try:
            await self._stdout_future
            return self._get_output()
        except Exception as e:
            raise e

    async def _schedule_run_command(
        self, command: str, expect_prompt: Optional[str]
    ) -> str:
        await TelnetConnection.send_command(self._writer, command)
        print(
            f"expect prompt is: {self.prompt if expect_prompt is None else expect_prompt}"
        )
        output = await self._reader.readuntil(
            self.prompt.encode("latin-1")
            if expect_prompt is None
            else expect_prompt.encode("latin-1")
        )
        output = output.decode("latin-1")  # Decode
        _, output = output.split("\n", 1)
        return output

    def _get_output(self) -> str:
        """
        Get the result of the running command

        Returns:
            Tuple contains the command, and result of that command, or None, plus host at the end

        Raises:
            InvalidStateError: When no command is running
        """
        # Check if the task is done, else return False and empty string
        if self.running_command is None:
            raise InvalidStateError("No running command")
        if e := self._stdout_future.exception() is not None:
            raise ConnectionError(
                f"DEBUG: Exception when running command {self.running_command}: {e}"
            )

        result = self._stdout_future.result()
        print("result of command:", result)

        self._stdout_future = None
        self.running_command = None
        self.current_command_timeout = None

        return result

    @override
    async def close(self) -> None:
        self.running_command = None
        self._stdout_future = None
        self.current_command_timeout = None
        self._writer.close()
        self._reader.feed_eof()


class ConnectionFactory:
    @staticmethod
    async def new_connection(
        device: DeviceModel,
        credential: CredentialModel,
        client_keys: Optional[list[str]],
        connect_timeout: int,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    ) -> BaseConnection:
        connection_type = credential.connection_type
        try:
            if connection_type == ConnectionType.SSH:
                print("SSHing...")
                return await ConnectionFactory._new_ssh_connection(
                    device, credential, client_keys, connect_timeout, idle_timeout
                )
            elif connection_type == ConnectionType.TELNET:
                return await ConnectionFactory._new_telnet_connection(
                    device, credential, connect_timeout, idle_timeout
                )
            else:
                raise ConnectionError(f"Unknown connection type: {connection_type}")
        except (TimeoutError, ConnectionError, Exception) as e:
            raise e

    @staticmethod
    async def _new_ssh_connection(
        device: DeviceModel,
        credential: CredentialModel,
        client_keys: Optional[list[str]],
        connect_timeout: int,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    ) -> BaseConnection:
        """
        Schedule a command to run on this connection

        Returns:
            The connection object (if connect success)

        Raises:
            ConnectionError: If connect fails
        """
        host = device.ip
        password = None if credential.password == "" else credential.password
        device_type = device.device_type
        # device_type = DeviceType.get_device_type(device_model.code)
        print(f"DeviceModel type: {device_type}")

        try:
            print("Connecting to device using SSH...")
            if client_keys is None:
                conn = await asyncssh.connect(
                    host=device.ip,
                    port=credential.port,
                    username=credential.username,
                    password=password,
                    known_hosts=None,
                    connect_timeout=connect_timeout,
                    encryption_algs="*",
                    kex_algs="*",
                )
            else:
                conn = await asyncssh.connect(
                    host=device.ip,
                    port=credential.port,
                    username=credential.username,
                    password=password,
                    client_keys=client_keys,
                    known_hosts=None,
                    connect_timeout=connect_timeout,
                    encryption_algs="*",
                    kex_algs="*",
                )

            if device_type == DeviceType.H3C:
                process = await conn.create_process(
                    term_type="ansi", encoding="latin-1"
                )
            else:
                process = await conn.create_process(
                    term_type="ansi", encoding="latin-1"
                )
            prompt = ">"

            # Prepare the connection
            if device_type != DeviceType.LINUX:
                print("wait for initial prompt")
                initial_response = await SSHConnection.expect_response(
                    process, SSHConnection.default_expect_prompts
                )
                if not initial_response:
                    raise ConnectionError(
                        f"Cannot connect to {host}, expected patterns: {SSHConnection.default_expect_prompts}, but got no response"
                    )

                print("init 1:", initial_response.encode())
                if "assword" in initial_response:
                    # Have to enter the password to login
                    process.stdin.write(f"{password}\n")
                    await process.stdin.drain()
                    initial_response = await SSHConnection.expect_response(
                        process, SSHConnection.default_expect_prompts
                    )
                    print("init 2:", initial_response.encode())
                    if prompt not in initial_response:
                        raise ConnectionError(
                            f"Cannot connect, may be the credential is incorrect. Server message: {initial_response}"
                        )

                logger.info("Get the last line as prompt")
                prompt = initial_response.split("\n")[-1]
                print(f"initial prompt: {prompt}")
                # if device_model.code not in prompt:
                #     raise ConnectionError(
                #         f"Wrong type of device, expected {device_model.code} but got {prompt}"
                #     )

                await ConnectionFactory._disable_paging(device_type, process, prompt)

            print("Done, returning connection...")

            return SSHConnection(
                connection=conn,
                process=process,
                device_type=device_type,
                idle_timeout=idle_timeout,
                host=host,
                prompt=prompt,
            )
        except TimeoutError as e:
            raise e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {host}: {str(e)}")

    @classmethod
    async def _disable_paging(
        cls, device_type: DeviceType, process: asyncssh.SSHClientProcess, prompt: str
    ) -> None:
        """
        Disable paging for the device, so that we can get the full output of the command

        Raises:
            TimeoutError: If the command to disable paging times out
            ConnectionError: If the command to disable paging fails
        """
        if device_type == DeviceType.HUAWEI:
            process.stdin.write("screen-length 0 temporary\n")
            output = await SSHConnection.expect_response(process, [prompt], timeout=15)

            # Run the scroll command instead
            if "error" in output:
                process.stdin.write("scroll\n")
                output = await SSHConnection.expect_response(
                    process, [prompt], timeout=15
                )

            # Error
            if output == "":
                raise TimeoutError(
                    "Failed to disable paging using command: screen-length 0 temporary, scroll, timeout while waiting for prompt"
                )
            if "error" in output:
                raise ConnectionError(
                    f"Failed to disable paging using command \n- screen-length 0 temporary\n- scroll 512\nOutput: {output}"
                )

            logger.debug(f"disable paging output: \n{output}")
            print(f"disable paging output: \n{output}")
        elif device_type == DeviceType.H3C:
            print("Disable paging for H3C: screen-length disable")
            process.stdin.write("screen-length disable\n")
            output = await SSHConnection.expect_response(process, [prompt], timeout=15)

            # Error
            if output == "":
                raise TimeoutError(
                    "Failed to disable paging using command: screen-length disable, timeout while waiting for prompt"
                )
            if "error" in output:
                raise ConnectionError(
                    f"Failed to disable paging using command \n- screen-length disable\nOutput: {output}"
                )

            logger.debug(f"disable paging output: \n{output}")
            print(f"disable paging output: \n{output}")
        else:
            return

    @classmethod
    async def _new_telnet_connection(
        cls,
        device: DeviceModel,
        credential: CredentialModel,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    ) -> BaseConnection:
        """
        Try to connect and authenticate using telnet

        Returns:
            The connection object (if connect success)

        Raises:
            TimeoutError: If connect timeout for some reason
        """
        reader: TelnetReader
        writer: TelnetWriter
        print(f"Getting device model with id: {credential.device_model_id}")
        # device_model = await get_device_model(credential.device_model_id)
        device_model = device.device_model
        print(f"Got device model: {device_model}")
        device_type = DeviceType.get_device_type(device_model.code)
        print(f"DeviceModel type: {device_type}")
        try:
            print(
                f"Try to connect to {device.ip} using telnet, port: {credential.port}"
            )
            reader, writer = await asyncio.wait_for(
                telnetlib3.open_connection(device.ip, credential.port),
                timeout=connect_timeout,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Timeout error (connect took longer than {connect_timeout} seconds)"
            )

        # await asyncio.sleep(1)  # Wait for negotiation?

        if credential.username is not None and credential.username:
            print("Doing authentication")
            try:
                await cls._authenticate_telnet(credential, reader, writer)
            except TimeoutError as e:
                raise e

        expect_prompts = (
            TelnetConnection.default_expect_prompts
            if "expect_prompts" not in credential.extra
            else [re.escape(pattern) for pattern in credential.extra["expect_prompts"]]
        )

        expect_errors = (
            TelnetConnection.default_expect_errors
            if "expect_prompts" not in credential.extra
            else [re.escape(pattern) for pattern in credential.extra["expect_errors"]]
        )

        # Get the prompt phrase
        logger.info("wait for initial prompt")
        response, pattern = await TelnetConnection.expect_response(
            reader, expect_prompts + expect_errors
        )
        match, pattern = _expect(response, expect_prompts + expect_errors)

        if not match:
            raise ConnectionError(
                f"Cannot connect to {device.ip}, expected patterns: {expect_prompts + expect_errors}, but got: {response.encode()}"
            )

        if pattern in TelnetConnection.default_expect_errors:
            raise ConnectionError(
                f"Failed to connect to {device.ip}: {response.encode()}"
            )

        prompt = response.split("\n")[-1]
        print(f"Prompt is {prompt}")

        return TelnetConnection(
            host=device.ip,
            reader=reader,
            writer=writer,
            device_type=device_type,
            prompt=prompt,
            idle_timeout=idle_timeout,
        )

    @classmethod
    async def _authenticate_telnet(
        cls,
        credential: CredentialModel,
        reader,
        writer,
        timeout=DEFAULT_CONNECT_TIMEOUT,
    ):
        """
        Authenticate

        Returns:
            The connection object (if connect success)

        Raises:
            TimeoutError: If connect timeout (cannot find the expected pattern)
        """
        expect_usernames = (
            TelnetConnection.default_expect_usernames
            if "expect_usernames" not in credential.extra
            else [
                re.escape(pattern) for pattern in credential.extra["expect_usernames"]
            ]
        )
        expect_passwords = (
            TelnetConnection.default_expect_passwords
            if "expect_passwords" not in credential.extra
            else [
                re.escape(pattern) for pattern in credential.extra["expect_passwords"]
            ]
        )
        # Authenticate:
        try:
            response_username_prompt, _ = await TelnetConnection.expect_response(
                reader, expect_usernames, timeout=timeout
            )
            # if not _expect(response_username_prompt, expect_usernames):

            print("response (expect username):", response_username_prompt.encode())
            print(f"login using username: {credential.username}")
            writer.write(credential.username + "\n")
            await writer.drain()

            response_password_prompt, _ = await TelnetConnection.expect_response(
                reader, expect_passwords, timeout=timeout
            )
            print("response (expect password):", response_password_prompt.encode())
            print(f"login using password: {credential.password}")
            writer.write(credential.password + "\n")
            await writer.drain()
        except TimeoutError as e:
            print(f"Timeout error when authenticate telnet: {e}")
            raise
