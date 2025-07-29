import pytest
import yt.wrapper as yt

from tractoray.internal.coordinator import (
    CoordinationInfo,
    HeadInfo,
)
from tractoray.internal.ray import (
    AriadneTransformer,
    RayInfo,
)


@pytest.fixture
def coordination_info() -> CoordinationInfo:
    head_info = HeadInfo(
        endpoint="head.example.com",
        port=6379,
        dashboard_port=8265,
        client_port=10001,
        job_id="0000-0000-000",
    )
    return CoordinationInfo(
        operation_url="http://proxy.example.com/operations/123",
        head=head_info,
        operation_id="123",
        readiness=[],
    )


def test_with_http_proxy(coordination_info: CoordinationInfo) -> None:
    yt_client = yt.YtClient(proxy="http://proxy.example.com")
    transformer = AriadneTransformer.create(yt_client)
    ray_info = RayInfo(coordination_info, yt_client, transformer)

    assert (
        ray_info.dashboard.address
        == "https://ariadne-http.proxy.example.com:443/_ariadne/exec_nodes/head.example.com/8265/"
    )
    assert ray_info.client.address == "ray://ariadne-grpc.proxy.example.com"


def test_without_http_prefix(coordination_info: CoordinationInfo) -> None:
    yt_client = yt.YtClient(proxy="proxy.example.com")
    transformer = AriadneTransformer.create(yt_client)
    ray_info = RayInfo(coordination_info, yt_client, transformer)

    assert (
        ray_info.dashboard.address
        == "https://ariadne-http.proxy.example.com:443/_ariadne/exec_nodes/head.example.com/8265/"
    )
    assert ray_info.client.address == "ray://ariadne-grpc.proxy.example.com"
