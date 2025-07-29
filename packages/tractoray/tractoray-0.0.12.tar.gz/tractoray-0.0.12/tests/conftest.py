import os
from pathlib import Path
import subprocess
from typing import Generator

import pytest
import yt.wrapper as yt

from tests.utils import (
    DOCKER_IMAGE,
    get_random_string,
)
from tests.yt_instances import (
    YtInstance,
    YtInstanceExternal,
    YtInstanceTestContainers,
)
from tractoray.ytpath import YtPath


@pytest.fixture(scope="session")
def yt_instance() -> Generator[YtInstance, None, None]:
    yt_mode = os.environ.get("YT_MODE", "testcontainers")
    if yt_mode == "testcontainers":
        with YtInstanceTestContainers() as yt_instance:
            yield yt_instance
    elif yt_mode == "external":
        proxy_url = os.environ["YT_PROXY"]
        yt_token = os.environ.get("YT_TOKEN")
        assert yt_token is not None
        yield YtInstanceExternal(proxy_url=proxy_url, token=yt_token)
    else:
        raise ValueError(f"Unknown yt_mode: {yt_mode}")


@pytest.fixture(scope="session")
def yt_base_dir(yt_instance: YtInstance) -> YtPath:
    yt_client = yt_instance.get_client()

    path = f"//tmp/tractoray_tests/run_{get_random_string(4)}"
    yt_client.create("map_node", path, recursive=True)
    return YtPath(path)


def _get_yt_path(yt_instance: YtInstance, yt_base_dir: YtPath) -> YtPath:
    yt_client = yt_instance.get_client()
    path = f"{yt_base_dir}/{get_random_string(8)}"
    yt_client.create("map_node", path)
    return YtPath(path)


@pytest.fixture(scope="function")
def yt_path(yt_instance: YtInstance, yt_base_dir: YtPath) -> YtPath:
    return _get_yt_path(yt_instance, yt_base_dir)


@pytest.fixture(scope="session")
def tractoray_path() -> Path:
    return (Path(__file__).parent.parent / "tractoray").resolve()


@pytest.fixture
def test_data_path() -> Path:
    return (Path(__file__).parent / "data").absolute()


@pytest.fixture(scope="session")
def ray_instance(
    yt_instance: YtInstance,
    yt_base_dir: YtPath,
    tractoray_path: Path,
) -> Generator[str, None, None]:
    yt_path = _get_yt_path(yt_instance, yt_base_dir)
    extra_commands = []
    if isinstance(yt_instance, YtInstanceTestContainers):
        extra_commands = ["--yt-proxy-in-job", "localhost:80"]
    start_process = subprocess.run(
        [
            "tractoray",
            "start",
            "--workdir",
            yt_path,
            "--node-count",
            "2",
            "--cpu-limit",
            "2",
            "--memory-limit",
            str(4 * 1024 * 1024 * 1024),
            "--env-var",
            "ENV_VAR_1=VALUE_1",
            "--env-var",
            "ENV_VAR_2=VALUE_2",
            "--tractoray-source-path",
            str(tractoray_path),
            "--docker-image",
            DOCKER_IMAGE,
            "--ray-head-params",
            "'--ray-debugger-external --disable-usage-stats'",
            "--ray-worker-params",
            "'--ray-debugger-external'",
            *extra_commands,
        ],
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
            "YT_LOG_LEVEL": "INFO",
        },
    )
    assert start_process.returncode == 0, start_process.stderr

    yield yt_path

    stop_process = subprocess.run(
        ["tractoray", "stop", "--workdir", yt_path],
        capture_output=True,
        text=True,
    )
    assert stop_process.returncode == 0
