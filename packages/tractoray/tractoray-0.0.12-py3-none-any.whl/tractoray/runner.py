from dataclasses import dataclass
import logging
import os
from pathlib import Path
import shlex
import shutil
import tempfile
import time

import yt.wrapper as yt
from yt.wrapper.operation_commands import OperationState

from tractoray.errors import RunError
from tractoray.internal.coordinator import (
    CoordinationInfo,
    CoordinationInfoFactory,
)
from tractoray.internal.logs import setup_logging
from tractoray.internal.ray import (
    AriadneTransformer,
    RayInfo,
)
from tractoray.ytpath import YtPath


_LOGGER = logging.getLogger(__name__)
_DEFAULT_TIMEOUT = 5.0
_DEFAULT_MEMORY_LIMIT = 32 * 1024 * 1024 * 1024
_DEFAULT_DOCKER_IMAGE: str = (
    "cr.eu-north1.nebius.cloud/e00faee7vas5hpsh3s/tractoray/default:2025-06-12-16-59-42-9a2ce5611"
)
_DEFAULT_CPU_LIMIT = 8
_DEFAULT_GPU_LIMIT = 0
_DEFAULT_POOL_TREES = ["default"]
_MAX_FAILED_JOB_COUNT = 100


@dataclass
class RunInfo:
    _operation_id: str
    _coordinator_path: YtPath
    _yt_client: yt.YtClient

    def get_coordination_info(self) -> CoordinationInfo | None:
        info = CoordinationInfoFactory(
            _yt_client=yt.YtClient(config=yt.default_config.get_config_from_env()),
            _coordinator_path=self._coordinator_path,
        ).get()
        if info and info.operation_id == self._operation_id and info.is_ready():
            return info
        return None

    def check_operation(self) -> None:
        current_operation_state: OperationState = self._yt_client.get_operation_state(
            self._operation_id,
        )
        if current_operation_state.is_unsuccessfully_finished():
            raise RunError(
                f"Current operation {self._operation_id} is failed",
            )

    @property
    def operation_url(self) -> str:
        url = yt.operation_commands.get_operation_url(
            self._operation_id,
            client=self._yt_client,
        )
        assert isinstance(url, str)
        return url


@dataclass
class YtRunner:
    _workdir: str
    _yt_client: yt.YtClient
    _node_count: int
    _docker_image: str
    _cpu_limit: int
    _gpu_limit: int
    _memory_limit: int
    _pool: str | None
    _pool_trees: list[str]
    _env_vars: list[tuple[str, str]]
    _log_level: str | None
    _ray_head_params: str
    _ray_worker_params: str
    _tractoray_source_path: str | None = None
    _yt_proxy_in_job: str | None = None

    def run(self) -> RunInfo:
        coordinator_path = YtPath(f"{self._workdir}/coordinator")
        info = CoordinationInfoFactory(
            _yt_client=self._yt_client,
            _coordinator_path=coordinator_path,
        ).get()
        if info and info.operation_id:
            prev_operation_state: OperationState = yt.get_operation_state(
                info.operation_id,
            )
            if prev_operation_state.is_running():
                operation_url = yt.operation_commands.get_operation_url(
                    info.operation_id,
                    client=self._yt_client,
                )
                raise RunError(
                    f"Previous operation {operation_url} is still running",
                )

        operation_spec = yt.VanillaSpecBuilder()
        head_task = self._make_head_task()
        node_task = self._make_node_task()
        if self._tractoray_source_path:
            tractoray_zip = self._pack_tractoray(Path(self._tractoray_source_path))
            head_task = self._add_tractoray_zip(head_task, tractoray_zip)
            node_task = self._add_tractoray_zip(node_task, tractoray_zip)

        operation_spec.task("head", head_task)
        operation_spec.task("node", node_task)

        operation_spec.title(f"ray {self._workdir}")
        operation_spec.secure_vault(
            {
                "USER_YT_TOKEN": self._yt_token,
            },
        )
        operation_spec.pool_trees(self._pool_trees)
        operation_spec.pool(self._pool)
        operation_spec.max_failed_job_count(_MAX_FAILED_JOB_COUNT)
        operation = self._yt_client.run_operation(operation_spec, sync=False)
        return RunInfo(
            _operation_id=operation.id,
            _coordinator_path=coordinator_path,
            _yt_client=self._yt_client,
        )

    def _pack_tractoray(self, source_path: Path) -> Path:
        temp_file = tempfile.TemporaryDirectory()
        temp_path = Path(temp_file.name).absolute()
        shutil.make_archive(str(temp_path), "zip", source_path.parent, "tractoray")
        return temp_path.with_suffix(".zip")

    def _add_tractoray_zip(
        self, spec: yt.TaskSpecBuilder, path: Path
    ) -> yt.TaskSpecBuilder:
        spec.add_file_path(
            yt.LocalFile(
                path.absolute(),
                file_name="tractoray.zip",
            ),
        )
        spec.environment_variable(
            "PYTHONPATH", "$PYTHONPATH:/slot/sandbox/tractoray.zip"
        )
        return spec

    def _make_env(self) -> dict[str, str]:
        user_env = {k: v for k, v in self._env_vars}
        env = {
            "YT_ALLOW_HTTP_REQUESTS_TO_YT_FROM_JOB": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            **user_env,
        }
        if self._log_level is not None:
            env["YT_LOG_LEVEL"] = self._log_level
        return env

    def _make_head_task(
        self,
    ) -> yt.TaskSpecBuilder:
        task_spec = yt.TaskSpecBuilder("head")
        command = [
            "python3 -m tractoray.cli.bootstrapper head",
            f"--workdir {shlex.quote(self._workdir)}",
            # node count here is a total node count in the cluster, including head node
            f"--node-count {self._node_count}",
            f"--cpu-limit {self._cpu_limit}",
            f"--proxy {self._yt_proxy_in_job or self._yt_proxy}",
            f"--ray-params={self._ray_head_params}",
        ]
        escaped_command = " ".join(command)
        _LOGGER.debug("Running command: %s", escaped_command)

        task_spec.command(escaped_command)
        task_spec.environment(self._make_env())
        task_spec.job_count(1)
        task_spec.docker_image(self._docker_image)
        task_spec.cpu_limit(self._cpu_limit)
        task_spec.port_count(6)
        task_spec.gpu_limit(self._gpu_limit)
        task_spec.memory_limit(self._memory_limit)
        return task_spec

    def _make_node_task(
        self,
    ) -> yt.TaskSpecBuilder:
        task_spec = yt.TaskSpecBuilder("node")
        node_count = self._node_count - 1  # head node is not counted
        if node_count <= 0:
            return task_spec
        command = [
            "python3 -m tractoray.cli.bootstrapper node",
            f"--workdir {shlex.quote(self._workdir)}",
            # node count here is a total node count in the cluster, including head node
            f"--node-count {self._node_count}",
            f"--cpu-limit {self._cpu_limit}",
            f"--proxy {self._yt_proxy_in_job or self._yt_proxy}",
            f"--ray-params={self._ray_worker_params}",
        ]
        escaped_command = " ".join(command)
        _LOGGER.debug("Running command: %s", escaped_command)

        task_spec.command(escaped_command)
        task_spec.environment(self._make_env())
        task_spec.job_count(node_count)
        task_spec.docker_image(self._docker_image)
        task_spec.cpu_limit(self._cpu_limit)
        task_spec.port_count(1)
        task_spec.gpu_limit(self._gpu_limit)
        task_spec.memory_limit(self._memory_limit)
        return task_spec

    @property
    def _yt_token(self) -> str:
        token = yt.http_helpers.get_token(client=self._yt_client)
        assert isinstance(token, str)
        return token

    @property
    def _yt_proxy(self) -> str:
        proxy = self._yt_client.config["proxy"]["url"]
        assert isinstance(proxy, str)
        return proxy


def _get_docker_image() -> str:
    return (
        os.environ.get("YT_BASE_LAYER")
        or os.environ.get("YT_JOB_DOCKER_IMAGE")
        or _DEFAULT_DOCKER_IMAGE
    )


def run(
    workdir: str,
    node_count: int = 1,
    docker_image: str | None = None,
    cpu_limit: int = _DEFAULT_CPU_LIMIT,
    gpu_limit: int = _DEFAULT_GPU_LIMIT,
    memory_limit: int = _DEFAULT_MEMORY_LIMIT,
    pool: str | None = None,
    pool_trees: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
    yt_client: yt.YtClient | None = None,
    ray_head_params: str = "",
    ray_worker_params: str = "",
) -> RayInfo:
    log_level = setup_logging()
    if pool_trees is None:
        pool_trees = _DEFAULT_POOL_TREES
    if docker_image is None:
        docker_image = _get_docker_image()

    if yt_client is None:
        yt_client = yt.YtClient(config=yt.default_config.get_config_from_env())

    if env_vars is None:
        env_vars = {}

    runner = YtRunner(
        _workdir=workdir,
        _yt_client=yt_client,
        _node_count=node_count,
        _docker_image=docker_image,
        _cpu_limit=cpu_limit,
        _gpu_limit=gpu_limit,
        _memory_limit=memory_limit,
        _pool=pool,
        _pool_trees=pool_trees,
        _env_vars=list(env_vars.items()),
        _log_level=log_level,
        _tractoray_source_path=None,
        _ray_head_params=ray_head_params,
        _ray_worker_params=ray_worker_params,
    )
    info = runner.run()
    while True:
        info.check_operation()
        coordination_info = info.get_coordination_info()
        if coordination_info:
            return RayInfo(
                _coordination_info=coordination_info,
                _yt_client=yt_client,
                _transformer=AriadneTransformer.create(yt_client),
            )
        time.sleep(_DEFAULT_TIMEOUT)
