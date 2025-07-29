from dataclasses import dataclass
import enum
import logging
import time

from yt import wrapper as yt

from tractoray.errors import CoordinatorError
from tractoray.ytpath import YtPath


COORDINATION_TIMEOUT = 1.0
_LOGGER = logging.getLogger(__name__)


class ReadinessStatus(str, enum.Enum):
    OK = "ok"
    UNKNOWN = "unknown"


@dataclass
class Coordinator:
    node_index: int
    self_endpoint: str
    head_endpoint: str
    head_port: int
    head_dashboard_port: int
    head_client_port: int

    def is_head(self) -> bool:
        return self.node_index == 0


@dataclass
class Barrier:
    _node_count: int
    _yt_client: yt.YtClient
    _coordinator_path: YtPath

    def _check_gang_barrier(self) -> bool:
        readiness = self._yt_client.get(f"{self._coordinator_path}/readiness")
        assert len(readiness) == self._node_count
        if any(el["status"] != ReadinessStatus.OK.value for el in readiness):
            return False
        return True

    def wait(self) -> None:
        _LOGGER.info("Waiting for all peers to start")
        while True:
            if self._check_gang_barrier():
                break
            time.sleep(COORDINATION_TIMEOUT)


@dataclass
class HeadCoordinatorFactory:
    _self_endpoint: str
    _node_index: int
    _node_count: int
    _coordinator_path: YtPath

    _yt_client: yt.YtClient
    _operation_id: str

    _head_port: int
    _head_job_id: str
    _public_dashboard_port: int
    _client_port: int

    _wait_barrier: bool = True

    def make(self) -> "Coordinator":
        _LOGGER.info("Running head node")
        with self._yt_client.Transaction():
            factory = CoordinationInfoFactory(
                _coordinator_path=self._coordinator_path,
                _yt_client=self._yt_client,
            )
            current_state = factory.get()
            if current_state:
                _LOGGER.info("Coordinator state: %s", current_state)
                if str(current_state.operation_id) != str(self._operation_id):
                    operation_state: yt.operation_commands.OperationState = (
                        self._yt_client.get_operation_state(current_state.operation_id)
                    )
                    if operation_state.is_running():
                        raise CoordinatorError(
                            f"Previous operation {current_state.operation_id} is still running",
                        )
            self._yt_client.create(
                "document",
                self._coordinator_path,
                force=True,
            )
            self._yt_client.lock(
                self._coordinator_path,
                mode="exclusive",
                waitable=False,
            )
            self._yt_client.set(
                self._coordinator_path,
                {},
            )
            self._yt_client.set(
                f"{self._coordinator_path}/operation_id",
                self._operation_id,
            )
            self._yt_client.set(
                f"{self._coordinator_path}/ray",
                {
                    "head": {
                        "endpoint": self._self_endpoint,
                        "port": self._head_port,
                        "job_id": self._head_job_id,
                        "dashboard_port": self._public_dashboard_port,
                        "client_port": self._client_port,
                    },
                },
            )
            readiness = [
                {
                    "node": self._self_endpoint,
                    "status": ReadinessStatus.OK.value,
                },
            ] + [{"node": "", "status": ReadinessStatus.UNKNOWN.value}] * (
                self._node_count - 1
            )
            self._yt_client.set(f"{self._coordinator_path}/readiness", readiness)

        if self._wait_barrier:
            Barrier(
                _node_count=self._node_count,
                _yt_client=self._yt_client,
                _coordinator_path=self._coordinator_path,
            ).wait()
        _LOGGER.info("Head node started")
        return Coordinator(
            node_index=self._node_index,
            self_endpoint=self._self_endpoint,
            head_endpoint=self._self_endpoint,
            head_port=self._head_port,
            head_dashboard_port=self._public_dashboard_port,
            head_client_port=self._client_port,
        )


@dataclass
class ReadinessInfo:
    node: str
    status: ReadinessStatus


@dataclass
class HeadInfo:
    endpoint: str
    port: int
    job_id: str
    dashboard_port: int
    client_port: int


@dataclass
class CoordinationInfo:
    head: HeadInfo
    operation_id: str
    operation_url: str
    readiness: list[ReadinessInfo]

    def is_ready(self) -> bool:
        return (
            all(el.status == ReadinessStatus.OK.value for el in self.readiness)
            and len(self.readiness) > 0
        )


@dataclass
class CoordinationInfoFactory:
    _coordinator_path: YtPath
    _yt_client: yt.YtClient

    def get(self) -> CoordinationInfo | None:
        if not self._yt_client.exists(self._coordinator_path):
            _LOGGER.debug("No coordinator file")
            return None
        state = self._yt_client.get(self._coordinator_path)
        if not state:
            _LOGGER.debug("Empty coordinator's state")
            return None
        _LOGGER.debug("Coordinator's state: %s", state)
        raw_head_info = state.get("ray").get("head")
        if not raw_head_info:
            return None
        return CoordinationInfo(
            head=HeadInfo(
                endpoint=str(raw_head_info["endpoint"]),
                port=int(raw_head_info["port"]),
                dashboard_port=int(raw_head_info["dashboard_port"]),
                client_port=int(raw_head_info["client_port"]),
                job_id=str(
                    raw_head_info.get("job_id", "000-000")
                ),  # default job_id for backward compatibility
            ),
            operation_id=state.get("operation_id"),
            operation_url=yt.operation_commands.get_operation_url(
                state.get("operation_id"), client=self._yt_client
            ),
            readiness=[
                ReadinessInfo(
                    node=el["node"],
                    status=ReadinessStatus(el["status"]),
                )
                for el in state.get("readiness", [])
            ],
        )


@dataclass
class WorkerCoordinatorFactory:
    _self_endpoint: str
    _node_index: int
    _node_count: int
    _coordinator_path: YtPath

    _yt_client: yt.YtClient
    _operation_id: str

    _wait_barrier: bool = True

    def make(self) -> "Coordinator":
        _LOGGER.info("Running worker node")
        factory = CoordinationInfoFactory(
            _coordinator_path=self._coordinator_path,
            _yt_client=self._yt_client,
        )
        while True:
            info = factory.get()
            if info and info.operation_id == self._operation_id:
                break
            time.sleep(COORDINATION_TIMEOUT)
        self._yt_client.set(
            f"{self._coordinator_path}/readiness/{self._node_index}",
            {
                "node": self._self_endpoint,
                "status": ReadinessStatus.OK.value,
            },
        )
        if self._wait_barrier:
            Barrier(
                _node_count=self._node_count,
                _yt_client=self._yt_client,
                _coordinator_path=self._coordinator_path,
            ).wait()
        _LOGGER.info("Worker node started")
        return Coordinator(
            node_index=self._node_index,
            self_endpoint=self._self_endpoint,
            head_port=info.head.port,
            head_endpoint=info.head.endpoint,
            head_dashboard_port=info.head.dashboard_port,
            head_client_port=info.head.client_port,
        )
