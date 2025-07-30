import asyncio
import logging
from pathlib import Path
from typing import Any
from typing import Optional

from formica.connection.connection import BaseConnection
from formica.connection.connection import ConnectionFactory
from formica.models.constant import CONNECTION_MAX_RETRIES
from formica.models.constant import CONNECTION_RETRY_SLEEP
from formica.models.constant import ConnectionType
from formica.models.constant import DEFAULT_COMMAND_TIMEOUT
from formica.models.constant import DEFAULT_CONNECT_TIMEOUT
from formica.models.constant import DEFAULT_IDLE_TIMEOUT
from formica.models.models import DeviceModel
from formica.node.nodes import BaseNode
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


class Context:
    """Chứa context của DeviceRun"""

    def __init__(
        self, flow, session: AsyncSession, log_file_path: Path, device: DeviceModel
    ):
        self.device = device
        self._connection: Optional[BaseConnection] = None
        self._flow = flow
        self.session = session
        self._log_file_path = log_file_path

    def get_node_by_id(self, node_id: str) -> Optional[BaseNode]:
        return self._flow.node_dict.get(node_id)

    def get_variables(self) -> dict:
        """Get the variables of the flow up to this point."""
        return self._flow.vars

    def set_node_output(self, node_id: str, output: Any):
        self._flow.vars[node_id] = {}
        self._flow.vars[node_id]["output"] = output

    def append_log(self, log: Optional[str]) -> None:
        if log is None:
            return

        with open(self._log_file_path, "a", encoding="utf-8") as f:
            f.write(log)
            pass

    async def make_connection(
        self,
        connection_type: ConnectionType,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    ) -> None:
        """
        Try to make a connection to the device using all the credentials provided.

        Args:
            connection_type: Type of connection to establish (e.g., SSH, Telnet)
            connect_timeout: Timeout for establishing a connection
            idle_timeout: Timeout for idle connections

        Raises:
            ValueError: conn_type is not supported
            ConnectionError: If all credentials fail to connect
        """
        credentials = [
            credential
            for credential in self.device.credentials
            if credential.connection_type == connection_type
        ]

        if len(credentials) == 0:
            raise ValueError(
                f"No credentials found for device {self.device.device_id} connection type: {connection_type}"
            )

        exceptions = ""
        for credential in credentials:
            client_keys = (
                None
                if "client_keys" not in credential.extra
                else credential.extra["client_keys"]
            )

            error_string_appended = False
            # Allow retry if there is exception (mainly to avoid key exchange hash mismatch)
            for try_number in range(CONNECTION_MAX_RETRIES):
                try:
                    print(f"Connect to {self.device.ip}, try number: {try_number + 1}")
                    conn = await ConnectionFactory.new_connection(
                        device=self.device,
                        credential=credential,
                        client_keys=client_keys,
                        connect_timeout=connect_timeout,
                        idle_timeout=idle_timeout,
                    )
                    self._connection = conn
                    return
                except ConnectionError as e:
                    import traceback

                    traceback.print_exc()
                    error_string = f"Can't connect to host: {self.device.ip} with credential: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.warning(error_string)

                    if not error_string_appended:
                        exceptions += f"- {error_string}"
                        error_string_appended = True
                except TimeoutError as e:
                    import traceback

                    traceback.print_exc()
                    error_string = f"Can't connect to host: {self.device.ip} with credential by {credential.connection_type}: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.warning(error_string)
                    exceptions += f"- {error_string}"
                    print("Timeout, so break")
                    break
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    error_string = f"Unexpected error connecting to host: {self.device.ip} with credential by {credential.connection_type}: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.error(error_string)

                    if not error_string_appended:
                        exceptions += f"- {error_string}"
                        error_string_appended = True

                await asyncio.sleep(CONNECTION_RETRY_SLEEP)

            logger.info("Trying next credential (if any)...")

        # All credential have failed
        raise ConnectionError(
            f"Couldn't connect to {self.device.ip} with all the credentials, exceptions:\n{exceptions}"
        )

    async def run_command(
        self,
        command: str,
        expect_prompt: Optional[str] = None,
        timeout=DEFAULT_COMMAND_TIMEOUT,
    ) -> str:
        """
        Run a command on the device and return the output.

        Args:
            command: The command to run on the device.
            expect_prompt: The prompt to expect after the command output (e.g. "#")
            timeout: Timeout for executing the command

        Returns:
            The output of the command.
        """

        if self._connection is None:
            raise ValueError(
                f"Error running command {command}: There's no connection established to device {self.device.device_id}."
            )

        try:
            return await self._connection.run_command(
                command, expect_prompt, timeout=timeout
            )
        except Exception as e:
            raise e

    async def discard_connection(self):
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
