import abc
from dataclasses import dataclass
import json
import logging
import os
import shlex
import subprocess
import sys

import yt.wrapper as yt

from tractoray.errors import RayBootstrapError
from tractoray.internal.coordinator import CoordinationInfo
from tractoray.internal.utils import (
    canonize_proxy,
    split_proxy,
)


RAY_CHECK_TIMEOUT = 5
_LOGGER = logging.getLogger(__name__)


@dataclass
class HeadNode:
    _self_endpoint: str
    _cpu_limit: int
    _head_port: int
    _dashboard_port: int
    _dashboard_agent_listen_port: int
    _public_dashboard_port: int
    _client_port: int
    _runtime_env_agent_port: int
    _ray_params: str

    _yt_client: yt.YtClient

    def run(self) -> None:
        # will be replaced with custom proxy with auth
        command = [
            "socat",
            f"TCP6-LISTEN:{self._dashboard_agent_listen_port},reuseaddr,ipv6only,fork",
            f"TCP4:127.0.0.1:{self._dashboard_agent_listen_port}",
        ]
        # dont wait, don't check
        subprocess.Popen(command, stdout=sys.stderr, stderr=sys.stderr)

        # will be replaced with custom proxy with auth
        command = [
            "socat",
            f"TCP6-LISTEN:{self._runtime_env_agent_port},reuseaddr,ipv6only,fork",
            f"TCP4:127.0.0.1:{self._runtime_env_agent_port}",
        ]
        # dont wait, don't check
        subprocess.Popen(command, stdout=sys.stderr, stderr=sys.stderr)

        # will be replaced with custom proxy with auth
        command = [
            "socat",
            f"TCP6-LISTEN:{self._public_dashboard_port},reuseaddr,fork",
            f"TCP4:127.0.0.1:{self._dashboard_port}",
        ]
        # dont wait, don't check
        subprocess.Popen(command, stdout=sys.stderr, stderr=sys.stderr)

        command = [
            "ray",
            "start",
            "--head",
            "--node-ip-address",
            self._self_endpoint,
            "--port",
            str(self._head_port),
            "--ray-client-server-port",
            str(self._client_port),
            "--runtime-env-agent-port",
            str(self._runtime_env_agent_port),
            "--include-dashboard",
            "true",
            "--dashboard-host",
            "127.0.0.1",
            "--dashboard-port",
            str(self._dashboard_port),
            "--dashboard-agent-listen-port",
            str(self._dashboard_agent_listen_port),
            "--num-cpus",
            str(self._cpu_limit),
            "--block",
            "-v",
            *shlex.split(self._ray_params),
        ]
        _LOGGER.info("Head command %s", command)
        env = {
            **os.environ,
        }
        process = subprocess.Popen(
            command, stdout=sys.stderr, stderr=sys.stderr, env=env
        )
        process.wait()
        if process.returncode != 0:
            raise RayBootstrapError("Can't start head node")


@dataclass
class WorkerNode:
    _cpu_limit: int
    _head_endpoint: str
    _head_port: int
    _self_endpoint: str
    _runtime_env_agent_port: int
    _ray_params: str

    def run(self) -> None:
        # will be replaced with custom proxy with auth
        command = [
            "socat",
            f"TCP6-LISTEN:{self._runtime_env_agent_port},reuseaddr,ipv6only,fork",
            f"TCP4:127.0.0.1:{self._runtime_env_agent_port}",
        ]
        # dont wait, don't check
        subprocess.Popen(command, stdout=sys.stderr, stderr=sys.stderr)

        env = {
            **os.environ,
        }

        command = [
            "ray",
            "start",
            "--node-ip-address",
            self._self_endpoint,
            "--address",
            f"{self._head_endpoint}:{self._head_port}",
            "--num-cpus",
            str(self._cpu_limit),
            "--runtime-env-agent-port",
            str(self._runtime_env_agent_port),
            "--block",
            "-v",
            *shlex.split(self._ray_params),
        ]
        _LOGGER.info("Run worker command %s", command)
        process = subprocess.Popen(
            command, stdout=sys.stderr, stderr=sys.stderr, env=env
        )
        process.wait()
        if process.returncode != 0:
            raise RayBootstrapError("Can't start worker node")


@dataclass
class RayDashboardConnection:
    env: dict[str, str]
    address: str


@dataclass
class RayClientConnection:
    metadata: list[tuple[str, str]]
    address: str


class Transformer(abc.ABC):
    @abc.abstractmethod
    def get_dashboard(self, host: str, port: int) -> RayDashboardConnection:
        pass

    @abc.abstractmethod
    def get_client(self, host: str, port: int) -> RayClientConnection:
        pass


@dataclass
class EmptyTransformer(Transformer):
    def get_dashboard(self, host: str, port: int) -> RayDashboardConnection:
        return RayDashboardConnection(
            address=f"{host}:{port}/",
            env={},
        )

    def get_client(self, host: str, port: int) -> RayClientConnection:
        return RayClientConnection(
            address=f"ray://{host}{port}",
            metadata=[],
        )


@dataclass
class AriadneTransformer(Transformer):
    _token: str
    _ariadne_http: str
    _ariadne_grpc: str

    @classmethod
    def create(cls, client: yt.YtClient) -> "AriadneTransformer":
        proxy = canonize_proxy(client.config["proxy"]["url"])
        token = yt.http_helpers.get_token(client=client)
        return AriadneTransformer(
            _token=token,
            _ariadne_http=f"https://ariadne-http.{proxy}",
            _ariadne_grpc=f"ariadne-grpc.{proxy}",
        )

    def get_dashboard(self, host: str, port: int) -> RayDashboardConnection:
        address = f"{self._ariadne_http}:443/_ariadne/exec_nodes/{host}/{port}/"
        return RayDashboardConnection(
            address=address,
            env={
                "RAY_JOB_HEADERS": json.dumps(
                    {"Authorization": f"OAuth {self._token}"}
                ),
                "RAY_ADDRESS": address,
            },
        )

    def get_client(self, host: str, port: int) -> RayClientConnection:
        return RayClientConnection(
            address=f"ray://{self._ariadne_grpc}",
            metadata=[
                ("authorization", f"OAuth {self._token}"),
                ("x-target-host", host),
                ("x-target-port", str(port)),
            ],
        )


@dataclass
class RayInfo:
    _coordination_info: CoordinationInfo
    _yt_client: yt.YtClient
    _transformer: Transformer

    @property
    def operation_url(self) -> str:
        return self._coordination_info.operation_url

    @property
    def dashboard(self) -> RayDashboardConnection:
        return self._transformer.get_dashboard(
            host=self._coordination_info.head.endpoint,
            port=self._coordination_info.head.dashboard_port,
        )

    @property
    def client(self) -> RayClientConnection:
        return self._transformer.get_client(
            host=self._coordination_info.head.endpoint,
            port=self._coordination_info.head.client_port,
        )

    @property
    def head_node_terminal_url(self) -> str:
        proxy = canonize_proxy(self._yt_client.config["proxy"]["url"])
        cluster_name, _ = split_proxy(proxy)
        return f"https://{proxy}/{cluster_name}/job/{self._coordination_info.operation_id}/{self._coordination_info.head.job_id}/extra_terminal"

    @property
    def head_node_job_shell_command(self) -> str:
        return f"yt run-job-shell {self._coordination_info.head.job_id}"

    @property
    def dashboard_instruction(self) -> str:
        return f"""
To get access the dashboard open the link: {self.dashboard.address}"""

    @property
    def client_instruction(self) -> str:
        return f"""
To get access to the ray cluster using ray client:

import ray
ray.init(
    address="{self.client.address}",
    _metadata={self.client.metadata},
)"""

    @property
    def cli_instruction(self) -> str:
        env = " ".join(f"{k}='{v}'" for k, v in self.dashboard.env.items())
        return f"""
To get access to the ray cluster using ray cli:

export {env}
ray job submit --working-dir . -- python3 your_script.py --no-wait
ray job logs raysubmit_hFndvmkyinHD9Fnk"""

    @property
    def head_node_connect_instruction(self) -> str:
        proxy = canonize_proxy(self._yt_client.config["proxy"]["url"])
        cluster_name, _ = split_proxy(proxy)
        return f"""
To access the terminal on the head node: {self.head_node_terminal_url}

To connect to the job shell on the head node run:
{self.head_node_job_shell_command}
(you should run `pip install tornado` to use this command)."""

    @property
    def instruction(self) -> str:
        return f"""# Dashboard
{self.dashboard_instruction}


# Connecting by Ray CLI
{self.cli_instruction}


# Connecting by Ray Client
{self.client_instruction}


# Connect to the head node terminal
{self.head_node_connect_instruction}
        """
