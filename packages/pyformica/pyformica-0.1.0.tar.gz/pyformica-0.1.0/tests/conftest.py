import json
import logging
import multiprocessing
from datetime import datetime
from datetime import timedelta
from time import sleep

import paramiko
import pytest
import pytest_asyncio
from formica import settings
from formica.db.models import DeviceModel
from formica.db.models import DeviceRunModel
from formica.db.models import FlowModel
from formica.db.models import FlowRunModel
from formica.db.models import FlowVersionModel
from formica.db.models import TaskModel
from formica.executor.executor import LocalExecutor
from formica.main import standalone
from formica.scheduler.scheduler import Scheduler
from formica.settings import config
from formica.settings import engine
from formica.utils.constant import DeviceRunState
from formica.utils.constant import FlowRunState
from formica.utils.constant import FlowRunType
from formica.web.main import run_webserver
from paramiko.ssh_exception import SSHException
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


logger = logging.getLogger(__name__)
# TODO: Xem lại các session trong khi test, có thể dùng ít session hơn được ko?


def pytest_configure():
    multiprocessing.set_start_method("spawn")


@pytest.fixture(scope="function")
def formica_standalone():
    # process = subprocess.Popen(["formica", "standalone"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process = multiprocessing.Process(target=standalone)
    print("Starting formica standalone...")
    process.start()

    yield process
    logger.info("Stopping formica standalone...")
    process.terminate()


@pytest.fixture(scope="function")
def connect_test_ssh_client():
    key_file = config["ssh_server"]["key_filepath"]
    key_file = None if key_file == "" else key_file

    client = paramiko.SSHClient()

    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if key_file is not None:
            paramiko.RSAKey(filename=key_file)
        client.connect(
            hostname=config["ssh_server"]["host"],
            username=config["ssh_server"]["username"],
            key_filename=key_file,
            port=config["ssh_server"]["port"],
            password=(
                config["ssh_server"]["password"]
                if config["ssh_server"]["password"] != ""
                else None
            ),
        )

        yield client
    except Exception as e:
        raise e
    finally:
        client.close()


@pytest.fixture(scope="function")
def clean_up_remote_test_files(connect_test_ssh_client):
    """Sau khi test xong thì xóa dữ liệu trong thư mục test ở máy remote"""
    yield

    try:
        logger.info("Try removing test files on remote server...")
        stdin, stdout, stderr = connect_test_ssh_client.exec_command(
            "rm formica_test/*"
        )
        logger.info("Removed")
        stdin.close()
    except SSHException:
        logger.error("Can't clean up files on remote test server")


@pytest.fixture(scope="session")
def time_constant():
    return {
        "5_MINUTES_BEFORE": datetime.now() - timedelta(minutes=5),
        "5_SECONDS_BEFORE": datetime.now() - timedelta(seconds=5),
        "1_HOUR_AFTER": datetime.now() + timedelta(hours=1),
        "4_MINUTES_BEFORE": datetime.now() - timedelta(minutes=4),
        "8_HOURS_INTERVAL": timedelta(hours=8),
    }


@pytest.fixture(scope="session")
def sample_flow_structures():
    with open("tests/sample_flow.json", "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="package")
def host():
    return "http://localhost:8000"


@pytest.fixture(scope="package")
def api_server():
    # Chạy Webserver
    process = multiprocessing.Process(target=run_webserver, daemon=True)
    print("Staring API server in as a daemon...")
    process.start()

    # Chờ api server khởi động?
    sleep(1)


@pytest.fixture(scope="module")
def scheduler():
    return Scheduler(LocalExecutor(), multi_processing=False)


@pytest_asyncio.fixture(scope="function")
async def session():
    async with settings.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("create all the tables...")
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session
        await conn.run_sync(SQLModel.metadata.drop_all)


# @pytest.fixture(scope="function")
# def resource_mock_data(session):
#     # Tạo ResourceModel
#     test_ssh_conn_ec2 = ResourceModel(
#         rs_id="test_ssh_conn_ec2",
#         rs_type="ssh",
#         description="Kết nối SSH tới EC2 dùng cho testing",
#         host=config["ssh_server"]["host"],
#         schema_=None,
#         login=config["ssh_server"]["username"],
#         password=(
#             config["ssh_server"]["password"]
#             if config["ssh_server"]["password"] != ""
#             else None
#         ),
#         port=int(config["ssh_server"]["port"]),
#         priority=0,
#         extra={"key_file": config["ssh_server"]["key_filepath"]},
#     )
#     print(f"ENV KEY FILE: {config['ssh_server']['key_filepath']}")
#
#     # Tạo ResourceSetModel
#     session.add(test_ssh_conn_ec2)
#     session.commit()
#     return test_ssh_conn_ec2


@pytest_asyncio.fixture(scope="function")
async def groups_mock(session):
    device = DeviceModel()


@pytest_asyncio.fixture(scope="function")
async def scheduling_flow_version_mock(
    resource_mock_data, sample_flow_structures, session
):
    scheduling_flow = FlowModel(
        flow_id="scheduling_flow",
        description="Flow đã có đã có FlowRun được tạo nhưng chưa được Scheduler xử lý",
    )
    scheduling_flow_version = FlowVersionModel(
        flow_id=scheduling_flow.flow_id,
        version="v1",
        structure=sample_flow_structures["test_ssh_2_commands"],
        description="Phiên bản flow đã tạo 1 FlowRun",
    )
    session.add(scheduling_flow)
    session.add(scheduling_flow_version)
    await session.commit()
    return scheduling_flow_version


@pytest.fixture(scope="function")
def running_flow_version_mock(resource_mock_data, sample_flow_structures, session):
    running_flow = FlowModel(
        flow_id="running_flow", description="Flow có FlowRun đang chạy"
    )
    running_flow_version = FlowVersionModel(
        flow_id=running_flow.flow_id,
        version="v1:running",
        structure=sample_flow_structures["test_ssh_2_commands"],
        description="Phiên bản FlowRun đang được chạy hoặc chuẩn bị hoàn thành",
    )
    session.add(running_flow)
    session.add(running_flow_version)
    session.commit()
    return running_flow_version


@pytest.fixture(scope="function")
def scheduling_manual_flowrun_mock(scheduling_flow_version_mock, session):
    scheduling_manual_flowrun = FlowRunModel(
        flow_id=scheduling_flow_version_mock.flow_id,
        version=scheduling_flow_version_mock.version,
        flow_run_id="scheduling_manual_flowrun",
        device_id="",
        description="FLowRun dạng manual vừa được tạo, chưa được schedule",
        run_type=FlowRunType.MANUAL,
    )
    session.add(scheduling_manual_flowrun)
    session.commit()
    return scheduling_manual_flowrun


@pytest.fixture(scope="function")
def late_schedule_flowrun_mock(scheduling_flow_version_mock, time_constant, session):
    late_schedule_flowrun = FlowRunModel(
        flow_id=scheduling_flow_version_mock.flow_id,
        version=scheduling_flow_version_mock.version,
        flow_run_id="late_schedule_flowrun",
        start_time=time_constant["5_SECONDS_BEFORE"],
        scheduling_interval=time_constant[
            "8_HOURS_INTERVAL"
        ].seconds,  # Một khoảng thời gian dài bất kỳ
        next_retry_run=time_constant["5_SECONDS_BEFORE"],
        descripion="FlowRun dạng schedule vừa được tạo, đã đến lúc schedule",
        run_type=FlowRunType.SCHEDULE,
    )
    session.add(late_schedule_flowrun)
    session.commit()
    return late_schedule_flowrun


@pytest.fixture(scope="function")
def early_schedule_flowrun_mock(scheduling_flow_version_mock, time_constant, session):
    early_schedule_flowrun = FlowRunModel(
        flow_id=scheduling_flow_version_mock.flow_id,
        version=scheduling_flow_version_mock.version,
        flow_run_id="early_schedule_flowrun",
        start_time=time_constant["1_HOUR_AFTER"],
        scheduling_interval=time_constant[
            "8_HOURS_INTERVAL"
        ].seconds,  # Một khoảng thời gian dài bất kỳ
        next_retry_run=time_constant["1_HOUR_AFTER"],
        description="FlowRun dạng schedule vừa được tạo, chưa đến lúc schedule",
        run_type=FlowRunType.SCHEDULE,
    )
    session.add(early_schedule_flowrun)
    session.commit()
    return early_schedule_flowrun


@pytest.fixture(scope="function")
def running_manual_flowrun_mock(running_flow_version_mock, time_constant, session):
    running_manual_flowrun = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_manual_flowrun",
        state=FlowRunState.RUNNING,
        start_time=time_constant["5_MINUTES_BEFORE"],
        description="FlowRun dạng manual đang chạy, DeviceRun hiện tại vẫn chưa hoàn thành",
        run_type=FlowRunType.MANUAL,
    )
    running_manual_device_run = DeviceRunModel(
        flow_id=running_manual_flowrun.flow_id,
        version=running_manual_flowrun.version,
        flow_run_id=running_manual_flowrun.flow_run_id,
        retry_run_id=f"manual__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        state=DeviceRunState.RUNNING,
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_time=time_constant["5_MINUTES_BEFORE"],
    )
    session.add(running_manual_flowrun)
    session.add(running_manual_device_run)
    session.commit()
    return running_manual_flowrun


@pytest.fixture(scope="function")
def running_schedule_flowrun_midway_mock(
    running_flow_version_mock, time_constant, session
):
    running_schedule_flowrun_midway = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_schedule_flowrun_midway",
        state=FlowRunState.RUNNING,
        start_time=time_constant["5_MINUTES_BEFORE"],
        schedule_interval=time_constant["8_HOURS_INTERVAL"].seconds,
        next_retry_run=time_constant["5_MINUTES_BEFORE"]
        + time_constant["8_HOURS_INTERVAL"],
        end_time=time_constant["5_MINUTES_BEFORE"] + time_constant["8_HOURS_INTERVAL"],
        description="FlowRun dạng schedule đang chạy, device_run hiện tại đã chạy thành công, vẫn có lần lập lịch chạy sắp tới",
        run_type=FlowRunType.SCHEDULE,
    )
    running_schedule_device_run_midway = DeviceRunModel(
        flow_id=running_schedule_flowrun_midway.flow_id,
        version=running_schedule_flowrun_midway.version,
        flow_run_id=running_schedule_flowrun_midway.flow_run_id,
        retry_run_id=f"schedule__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        state=DeviceRunState.RUNNING,
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_date=time_constant["5_MINUTES_BEFORE"],
    )
    session.add(running_schedule_flowrun_midway)
    session.add(running_schedule_device_run_midway)
    session.commit()
    return running_schedule_flowrun_midway


@pytest.fixture(scope="function")
def running_schedule_flowrun_final_mock(
    running_flow_version_mock, time_constant, session
):
    running_schedule_flowrun_final = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_schedule_flowrun_midway",
        state=FlowRunState.RUNNING,
        start_time=time_constant["5_MINUTES_BEFORE"],
        schedule_interval=time_constant["8_HOURS_INTERVAL"].seconds,
        next_retry_run=time_constant["5_MINUTES_BEFORE"]
        + time_constant["8_HOURS_INTERVAL"],
        end_time=time_constant["ONE_HOUR_AFTER"],
        description="FlowRun dạng schedule đang chạy, device_run hiện tại đã chạy thành công, không có lần lập lịch chạy sắp tới",
        run_type=FlowRunType.SCHEDULE,
    )
    running_schedule_device_run_final = DeviceRunModel(
        flow_id=running_schedule_flowrun_final.flow_id,
        version=running_schedule_flowrun_final.version,
        flow_run_id=running_schedule_flowrun_final.flow_run_id,
        retry_run_id=f"manual__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        state=DeviceRunState.RUNNING,
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_date=time_constant["5_MINUTES_BEFORE"],
    )
    session.add(running_schedule_flowrun_final)
    session.add(running_schedule_device_run_final)
    session.commit()
    return running_schedule_flowrun_final


@pytest.fixture(scope="function")
def running_success_manual_flowrun_mock(
    running_flow_version_mock, time_constant, session
):
    running_success_manual_flowrun = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_success_manual_flowrun",
        state=FlowRunState.RUNNING,
        start_time=time_constant["5_MINUTES_BEFORE"],
        description="FlowRun manual có device_run đã chạy xong, trạng thái thành công",
        run_type=FlowRunType.MANUAL,
    )
    success_manual_device_run = DeviceRunModel(
        flow_id=running_success_manual_flowrun.flow_id,
        version=running_success_manual_flowrun.version,
        flow_run_id=running_success_manual_flowrun.flow_run_id,
        retry_run_id=f"manual__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_date=time_constant["5_MINUTES_BEFORE"],
        end_time=time_constant["4_MINUTES_BEFORE"],
        duration=timedelta(minutes=1).seconds,
        state=DeviceRunState.SUCCESS,
    )
    session.add(running_success_manual_flowrun)
    session.add(success_manual_device_run)
    session.commit()
    return running_success_manual_flowrun


@pytest.fixture(scope="function")
def running_failed_will_retry_manual_flowrun_mock(
    running_flow_version_mock, time_constant, session
):
    running_failed_will_retry_flowrun = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_failed_will_retry_manual_flowrun",
        state=FlowRunState.RUNNING,
        max_retries=1,
        start_time=time_constant["5_MINUTES_BEFORE"],
        description="FlowRun manual đã chạy xong, trạng thái thất bại, vẫn còn lượt retry",
        run_type=FlowRunType.MANUAL,
    )
    failed_manual_device_run = DeviceRunModel(
        flow_id=running_failed_will_retry_flowrun.flow_id,
        version=running_failed_will_retry_flowrun.version,
        flow_run_id=running_failed_will_retry_flowrun.flow_run_id,
        retry_run_id=f"manual__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_date=time_constant["5_MINUTES_BEFORE"],
        end_time=time_constant["4_MINUTES_BEFORE"],
        duration=timedelta(minutes=1).seconds,
        state=DeviceRunState.FAILED,
    )
    session.add(running_failed_will_retry_flowrun)
    session.add(failed_manual_device_run)
    session.commit()
    return running_failed_will_retry_flowrun


@pytest.fixture(scope="function")
def running_failed_no_retry_manual_flowrun_mock(
    running_flow_version_mock, time_constant, session
):
    running_failed_no_retry_flowrun = FlowRunModel(
        flow_id=running_flow_version_mock.flow_id,
        version=running_flow_version_mock.version,
        flow_run_id="running_failed_no_retry_manual_flowrun",
        state=FlowRunState.RUNNING,
        start_time=time_constant["5_MINUTES_BEFORE"],
        description="FlowRun manual đã chạy xong, trạng thái thất bại, không còn lượt retry",
        run_type=FlowRunType.MANUAL,
    )
    failed_manual_retry_run = DeviceRunModel(
        flow_id=running_failed_no_retry_flowrun.flow_id,
        version=running_failed_no_retry_flowrun.version,
        flow_run_id=running_failed_no_retry_flowrun.flow_run_id,
        retry_run_id=f"manual__{time_constant['5_MINUTES_BEFORE'].strftime('%Y-%m-%dT%H:%M:%S')}",
        logical_start_time=time_constant["5_MINUTES_BEFORE"],
        actual_start_date=time_constant["5_MINUTES_BEFORE"],
        end_time=time_constant["4_MINUTES_BEFORE"],
        duration=timedelta(minutes=1).seconds,
        state=DeviceRunState.FAILED,
    )
    session.add(running_failed_no_retry_flowrun)
    session.add(failed_manual_retry_run)
    session.commit()
    return running_failed_no_retry_flowrun


@pytest.fixture(scope="function")
def queued_retry_run_mock(running_manual_flowrun_mock, session, sample_flow_structures):
    retry_run = running_manual_flowrun_mock.retry_runs[0]
    for node in sample_flow_structures["test_ssh_2_commands"]["nodes"]:
        session.add(
            TaskModel(
                retry_run_db_id=retry_run.retry_run_db_id,
                node_id=node["node_id"],
            )
        )
    return retry_run
