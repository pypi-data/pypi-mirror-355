from tests.yt_instances import YtInstance
from tractoray.internal.coordinator import (
    HeadCoordinatorFactory,
    WorkerCoordinatorFactory,
)
from tractoray.ytpath import YtPath


def test_coordinator(yt_instance: YtInstance, yt_path: YtPath) -> None:
    coordinator_path = YtPath(f"{yt_path}/coordinator")
    hf = HeadCoordinatorFactory(
        _self_endpoint="head.local",
        _node_index=0,
        _node_count=2,
        _coordinator_path=coordinator_path,
        _yt_client=yt_instance.get_client(),
        _operation_id="000000-0000-0000-000000000000",
        _wait_barrier=False,
        _head_port=12345,
        _head_job_id="000-000-0000",
        _public_dashboard_port=12346,
        _client_port=12347,
    )
    c = hf.make()
    print(c)
    wf = WorkerCoordinatorFactory(
        _self_endpoint="worker.local",
        _node_index=1,
        _node_count=2,
        _coordinator_path=coordinator_path,
        _yt_client=yt_instance.get_client(),
        _operation_id="000000-0000-0000-000000000000",
        _wait_barrier=True,
    )
    c = wf.make()
    print(c)
