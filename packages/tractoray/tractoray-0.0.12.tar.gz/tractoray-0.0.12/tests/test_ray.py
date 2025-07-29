import json
import os
import subprocess

from grpc import ssl_channel_credentials
import pytest
import ray
import requests
import yt.wrapper as yt

from tests.yt_instances import (
    YtInstance,
    YtInstanceTestContainers,
)


def test_tractoray_status_json(
    yt_instance: YtInstance,
    ray_instance: str,
    test_data_path: str,
) -> None:
    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", str(ray_instance), "--format", "json"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0

    parsed_status = json.loads(status_process.stdout)
    assert parsed_status["operation_url"]
    assert parsed_status["dashboard_url"]
    assert parsed_status["cli"]["env"]
    assert parsed_status["client"]["metadata"]
    assert parsed_status["client"]["address"]
    assert parsed_status["head"]["job_shell"]
    assert parsed_status["head"]["terminal_url"]


def test_tractoray_status_plaintext(
    yt_instance: YtInstance,
    ray_instance: str,
    test_data_path: str,
) -> None:
    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", str(ray_instance)],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0

    assert "Ray operation:" in status_process.stdout
    assert "export RAY_JOB_HEADERS=" in status_process.stdout
    assert "ray.init" in status_process.stdout
    assert "yt run-job-shell" in status_process.stdout
    assert "To access the terminal on the head node: https://"


def test_ray_cluster_status_not_found(
    yt_instance: YtInstance,
    yt_path: str,
) -> None:
    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", yt_path],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0
    assert "Ray cluster not found" in status_process.stdout


def test_ray_cli(
    yt_instance: YtInstance,
    ray_instance: str,
    test_data_path: str,
) -> None:
    if isinstance(yt_instance, YtInstanceTestContainers):
        pytest.skip("We don't have access to nodes in docker containers")
    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", str(ray_instance), "--format", "json"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0

    parsed_status = json.loads(status_process.stdout)
    submit_process = subprocess.run(
        [
            "ray",
            "job",
            "submit",
            "--working-dir",
            str(test_data_path),
            "--",
            "python3",
            "script.py",
        ],
        env={
            **os.environ,
            **parsed_status["cli"]["env"],
        },
        capture_output=True,
        text=True,
    )
    assert submit_process.returncode == 0
    for i in range(10):
        assert f"Task {i} has been completed on host" in submit_process.stdout
    assert " succeeded", status_process.stdout


def test_ray_dashboard(
    yt_instance: YtInstance,
    ray_instance: str,
) -> None:
    if isinstance(yt_instance, YtInstanceTestContainers):
        pytest.skip("We don't have access to nodes in docker containers")

    client = yt_instance.get_client()

    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", str(ray_instance), "--format", "json"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0

    parsed_status = json.loads(status_process.stdout)
    response = requests.get(
        parsed_status["dashboard_url"],
        headers={"Authorization": f"OAuth {yt.http_helpers.get_token(client=client)}"},
    )
    assert response.status_code == 200, response.text


def test_ray_client(
    yt_instance: YtInstance,
    ray_instance: str,
) -> None:
    if isinstance(yt_instance, YtInstanceTestContainers):
        pytest.skip("We don't have access to nodes in docker containers")

    status_process = subprocess.run(
        ["tractoray", "status", "--workdir", str(ray_instance), "--format", "json"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "YT_PROXY": yt_instance.get_client().config["proxy"]["url"],
            "YT_TOKEN": yt.http_helpers.get_token(client=yt_instance.get_client())
            or "",
        },
    )
    assert status_process.returncode == 0

    parsed_status = json.loads(status_process.stdout)
    ray_params = {
        "address": parsed_status["client"]["address"],
        "_metadata": parsed_status["client"]["metadata"],
    }
    if certs := os.environ.get("REQUESTS_CA_BUNDLE"):
        with open(certs, "rb") as f:
            trusted_certs = f.read()
        ray_params["_credentials"] = ssl_channel_credentials(
            root_certificates=trusted_certs,
        )
    ray.init(**ray_params)
    assert len(ray.nodes()) == 2
    ray.shutdown()
