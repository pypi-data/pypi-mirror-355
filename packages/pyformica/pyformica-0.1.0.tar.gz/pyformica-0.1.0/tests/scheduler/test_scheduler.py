from time import sleep

from formica.utils.constant import DeviceRunState
from formica.utils.constant import FlowRunState


def test_scheduling_manual_flowrun(scheduling_manual_flowrun_mock, scheduler, session):
    # FlowRun này phải chưa có DeviceRun nào được tạo ra từ nó
    assert not scheduling_manual_flowrun_mock.retry_runs

    scheduler.run(max_iteration=6, session=session)

    # Chờ cho Executor chạy DeviceRun xong?
    sleep(2)

    # Cập nhật lại FlowRun này

    session.add(scheduling_manual_flowrun_mock)
    session.refresh(scheduling_manual_flowrun_mock)

    # Trạng thái FlowRun phải chuyển qua FINISHED
    assert scheduling_manual_flowrun_mock.state == FlowRunState.FINISHED

    # Phải có RetryRun mới được tạo ra ứng với FlowRun này và có trạng thái là SUCCESS
    assert len(scheduling_manual_flowrun_mock.retry_runs) == 1
    retry_run = scheduling_manual_flowrun_mock.retry_runs[0]
    assert retry_run.state == DeviceRunState.SUCCESS

    # Phải có 4 TaskModel được tạo ra ứng với RetryRun này
    assert len(retry_run.tasks) == 4

    assert retry_run.state in [DeviceRunState.SUCCESS, DeviceRunState.FAILED]


# def test_early_schedule_flowrun(early_schedule_flowrun_mock, session):
#     assert not early_schedule_flowrun_mock.retry_runs
#
#     run_scheduler(max_iteration=1)
#
#     # Cập nhật lại FlowRun từ DB
#     session.refresh(early_schedule_flowrun_mock)
#
#     # Kết quả mong đợi là scheduler không làm gì cả
#     assert not early_schedule_flowrun_mock.retry_runs
#     assert early_schedule_flowrun_mock.state == FlowRunState.SUBMITTED


def test_running_manual_flow_run(running_manual_flowrun_mock, scheduler, session):
    # Phải có 1 RetryRun đang chạy, trạng thái RUNNING
    assert len(running_manual_flowrun_mock.retry_runs) == 1
    assert running_manual_flowrun_mock.retry_runs[0].state == DeviceRunState.RUNNING

    scheduler.run(max_iteration=3, session=session)

    # Cập nhật lại FlowRun này
    session.add(running_manual_flowrun_mock)
    session.refresh(running_manual_flowrun_mock)

    # Trạng thái FlowRun vẫn ko thay đổi
    assert len(running_manual_flowrun_mock.retry_runs) == 1
    assert running_manual_flowrun_mock.state == FlowRunState.RUNNING

    # RetryRun vẫn giữ nguyên trạng thái là RUNNING
    retry_run = running_manual_flowrun_mock.retry_runs[0]
    assert retry_run.state == DeviceRunState.RUNNING


def test_running_success_manual_flowrun(
    running_success_manual_flowrun_mock, scheduler, session
):
    # Phải có 1 RetryRun đang chạy, trạng thái SUCCESS
    session.add(running_success_manual_flowrun_mock)
    session.refresh(running_success_manual_flowrun_mock)
    assert len(running_success_manual_flowrun_mock.retry_runs) == 1
    assert (
        running_success_manual_flowrun_mock.retry_runs[0].state
        == DeviceRunState.SUCCESS
    )
    session.expunge(running_success_manual_flowrun_mock)

    scheduler.run(max_iteration=1)

    # Cập nhật lại FlowRun này
    session.add(running_success_manual_flowrun_mock)
    session.refresh(running_success_manual_flowrun_mock)

    # Trạng thái FlowRun phải chuyển qua FINISHED và chỉ có 1 RetryRun
    assert len(running_success_manual_flowrun_mock.retry_runs) == 1
    assert running_success_manual_flowrun_mock.state == FlowRunState.FINISHED

    # RetryRun vẫn giữ nguyên trạng thái là SUCCESS
    retry_run = running_success_manual_flowrun_mock.retry_runs[0]
    assert retry_run.state == DeviceRunState.SUCCESS


def test_running_failed_no_retry_manual_flowrun(
    running_failed_no_retry_manual_flowrun_mock, scheduler, session
):
    # Phải có 1 RetryRun đang chạy, trạng thái FAILED
    session.add(running_failed_no_retry_manual_flowrun_mock)
    session.refresh(running_failed_no_retry_manual_flowrun_mock)
    assert len(running_failed_no_retry_manual_flowrun_mock.retry_runs) == 1
    assert (
        running_failed_no_retry_manual_flowrun_mock.retry_runs[0].state
        == DeviceRunState.FAILED
    )
    session.expunge(running_failed_no_retry_manual_flowrun_mock)

    scheduler.run(max_iteration=1)

    # Cập nhật lại FlowRun này
    session.add(running_failed_no_retry_manual_flowrun_mock)
    session.refresh(running_failed_no_retry_manual_flowrun_mock)

    # Trạng thái FlowRun được cập nhật thành FINISHED
    assert len(running_failed_no_retry_manual_flowrun_mock.retry_runs) == 1
    assert running_failed_no_retry_manual_flowrun_mock.state == FlowRunState.FINISHED

    # RetryRun vẫn giữ nguyên trạng thái là FAILED
    retry_run = running_failed_no_retry_manual_flowrun_mock.retry_runs[0]
    assert retry_run.state == DeviceRunState.FAILED


def test_schedule_multiple_flowruns():
    # TODO: Chọn một vài flowrun cần được schedule ở trên để viết test này
    assert 1 == 1
