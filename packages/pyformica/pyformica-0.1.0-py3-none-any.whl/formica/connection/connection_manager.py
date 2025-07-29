import asyncio
import logging
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from nidus import db_service
from nidus.models import Device, Credential
from nidus.object.connection import ConnectionFactory, BaseConnection
from nidus.utils.constant import (
    ConnectionType,
    DEFAULT_CONNECT_TIMEOUT,
    MONITOR_IDLE_CONNECTION_INTERVAL,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_COMMAND_TIMEOUT,
    CONNECTION_MAX_RETRIES,
    CONNECTION_RETRY_SLEEP,
)
from nidus.session import NEW_SESSION

logger = logging.getLogger(__name__)


class ConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._connection_registry: dict[uuid.UUID, BaseConnection] = {}
            self._connect_tasks: dict[uuid.UUID, tuple[asyncio.Task, str]] = {}

            # logger.info("Starting monitoring idle connections")
            # print("starting monitoring idle connections")
            # loop = asyncio.get_event_loop()
            # self._monitoring_task = loop.create_task(self._monitor_idle_connections())

    # async def _start_monitoring(self):
    #     if not hasattr(self, "_monitoring_task") or self._monitoring_task.done():
    #         logger.info("Starting monitoring idle connections (ASGI)")
    #         self._monitoring_task = asyncio.create_task(
    #             self._monitor_idle_connections()
    #         )

    async def _monitor_idle_connections(self):
        await asyncio.sleep(MONITOR_IDLE_CONNECTION_INTERVAL)  # Check every 60 seconds

        # Get the connection that is idle timed out in connection registry
        idle_conn_ids = [
            conn_id
            for conn_id, conn_obj in self._connection_registry.items()
            if conn_obj.idle_timed_out()
        ]
        for conn_id in idle_conn_ids:
            logger.info(
                f"Detected idle connection: {conn_id} to host: {self._connection_registry[conn_id].host}"
            )

        tasks = [
            asyncio.create_task(self.connection_close(str(conn_id)))
            for conn_id in idle_conn_ids
        ]
        await asyncio.gather(*tasks)

    async def _try_connect(
        self,
        conn_id: uuid.UUID,
        device: Device,
        credentials: list[Credential],
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
    ) -> BaseConnection:
        """
        Try to make a connection to the device using all the credentials provided.
        Put that connection into the connection registry using the uuid passed in

        Args:
            conn_id: connection id
            device: The device to connect to
            credentials: List of credentials to use
            connect_timeout: Timeout for establishing a connection
            idle_timeout: Timeout for idle connections

        Returns:
            The prompt line

        Raises:
            ValueError: conn_type is not supported
        """
        print("credentials len:", len(credentials))

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
                    print(f"Connect to {device.ip}, try number: {try_number + 1}")
                    conn = await ConnectionFactory.new_connection(
                        device=device,
                        credential=credential,
                        client_keys=client_keys,
                        connect_timeout=connect_timeout,
                        idle_timeout=idle_timeout,
                    )
                    self._connection_registry[conn_id] = conn
                    return conn
                except ConnectionError as e:
                    error_string = f"Can't connect to host: {device.ip} with credential: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.warning(error_string)

                    if not error_string_appended:
                        exceptions += f"- {error_string}"
                        error_string_appended = True
                except TimeoutError as e:
                    error_string = f"Can't connect to host: {device.ip} with credential by {credential.connection_type}: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.warning(error_string)
                    exceptions += f"- {error_string}"
                    print("Timeout, so break")
                    break
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    error_string = f"Unexpected error connecting to host: {device.ip} with credential by {credential.connection_type}: username={credential.username}, password={credential.password}, key_file={client_keys}, exception: {e}"
                    logger.error(error_string)

                    if not error_string_appended:
                        exceptions += f"- {error_string}"
                        error_string_appended = True

                await asyncio.sleep(CONNECTION_RETRY_SLEEP)

            logger.info("Trying next credential (if any)...")

        # All credential have failed
        raise ConnectionError(
            f"Couldn't connect to {device.ip} with all the credentials, exceptions:\n{exceptions}"
        )

    async def device_connect(
        self,
        ip: str,
        conn_type: ConnectionType,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
        session: AsyncSession = NEW_SESSION,
    ) -> uuid.UUID | None:
        """
        Schedule the async function _try_connect() for execution

        Establish a connection to a device using specified connection type

        Args:
            ip: The ip of device to connect to
            conn_type: Type of connection to establish (SSH, etc.)
            connect_timeout: Timeout for establishing a connection
            idle_timeout: Timeout for idle connections
            session: The db session

        Returns:
            UUID of the established connection

        Raises:
            ConnectionError: If connection fails
            ValueError: If no credentials found or if connection type not supported
        """
        device = await db_service.get_device_by_ip(ip, session)
        if device is None:
            raise ValueError(f"Device with IP {ip} not found")
        credentials = device.device_model.credentials

        if len(credentials) == 0:
            raise ValueError(f"No credentials found for connection type: {conn_type}")

        conn_id = uuid.uuid4()
        connect_task = asyncio.create_task(
            self._try_connect(
                conn_id,
                device,
                credentials,
                connect_timeout,
                idle_timeout,
            )
        )

        logger.info(f"Schedule task connect to: {ip} with connection id: {conn_id}")
        self._connect_tasks[conn_id] = connect_task, ip

        return conn_id

    def get_host_by_connection_id(self, connection_id: str | None) -> str:
        """
        Get the host by connection id

        Args:
            connection_id: The connection id to get host

        Returns:
            The host of the connection
        """
        if connection_id is None:
            raise ValueError("Connection ID is None")
        key = uuid.UUID(connection_id)
        if key not in self._connect_tasks:
            raise ValueError(f"Connection not found for ID: {connection_id}")

        _, host = self._connect_tasks[key]
        return host

    def connection_status(self, connection_id: str) -> tuple[bool, str, str, str]:
        """
        Get status of a connection, mainly to check if the connection is established

        Args:
            connection_id: The connection id to get status

        Returns:
            Is the connection established?

        Raises:
            ConnectionError: If connection fails
        """
        key = uuid.UUID(connection_id)
        if key not in self._connect_tasks:
            raise ValueError(f"Connection not found for ID: {connection_id}")

        task, host = self._connect_tasks[key]
        if task.done():
            if exception := task.exception():
                # raise the ConnectionError (most likely)
                raise exception

            prompt = task.result().prompt
            # del self._connect_tasks[key]

            print(f"Connect task count: {len(self._connect_tasks)}")
            return True, "connected to the target host", host, prompt

        print(f"Connect task count: {len(self._connect_tasks)}")
        return False, "still trying to connect", host, ""

    async def run_command(
        self,
        connection_id: str,
        command: str,
        expect_prompt: str | None,
        timeout: float = DEFAULT_COMMAND_TIMEOUT,
    ) -> tuple[str, uuid.UUID]:
        """
        Create a task to execute a command on a connection

        Args:
            connection_id: UUID of the connection to execute the command on
            command: Command to execute
            expect_prompt: The prompt to expect after the command output (e.g. "#")
            timeout: Timeout for executing the command

        Returns:
            the host that this command is executed, and the connection_id

        Raises:
            ValueError: If connection not found
        """
        key = uuid.UUID(connection_id)
        if key not in self._connection_registry:
            raise ValueError(f"Connection not found for ID: {connection_id}")

        nidus_connection = self._connection_registry[key]
        await nidus_connection.run_command(command, expect_prompt, timeout=timeout)
        print("INFO: run command", command)
        await asyncio.sleep(1)

        return nidus_connection.host, key

    async def connection_output(
        self, connection_id: str
    ) -> tuple[str | None, str | None, str]:
        """
        Get the result of a task

        Args:
            connection_id: UUID of the task to get the result of

        Returns:
            Result of the task

        Raises:
            ValueError: If task not found
        """
        key = uuid.UUID(connection_id)
        if key not in self._connection_registry:
            raise ValueError(f"Connection not found for ID: {connection_id}")

        connection = self._connection_registry[key]
        try:
            output = connection.get_output()
            return output
        except TimeoutError as e:
            print(
                f"Timeout running command: {connection.running_command}, running more than {connection.current_command_timeout}"
            )
            raise e
        except Exception as e:
            raise e

    async def connection_close(self, conn_id: str) -> str:
        """
        Close a connection

        Args:
            conn_id: UUID of the connection to close

        Returns:
            the host name or IP of the device

        Raises:
            ValueError: If connection not found
        """
        key = uuid.UUID(conn_id)
        if key not in self._connection_registry:
            raise ValueError(f"Connection not found for ID: {conn_id}")

        connection = self._connection_registry[key]
        host = connection.host
        # TODO: Is there exception when closing?
        logger.info(f"Closing connection {conn_id} to host: {connection.host}")
        await connection.close()
        logger.info(f"Closed connection {conn_id} to host: {connection.host}")

        del self._connection_registry[key]
        del self._connect_tasks[key]
        return host

    def find_connection_ids_by_ip(self, host: str) -> list[uuid.UUID]:
        return [
            conn_id
            for conn_id, conn in self._connection_registry.items()
            if conn.host == host
        ]
