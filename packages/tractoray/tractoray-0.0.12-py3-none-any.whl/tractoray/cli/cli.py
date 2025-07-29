import argparse
import enum
import json
import logging
from pathlib import Path
import time

import yt.wrapper as yt
from yt.wrapper.operation_commands import OperationState

from tractoray.internal.coordinator import CoordinationInfoFactory
from tractoray.internal.logs import setup_logging
from tractoray.internal.ray import (
    AriadneTransformer,
    EmptyTransformer,
    RayInfo,
)
from tractoray.runner import (
    _DEFAULT_CPU_LIMIT,
    _DEFAULT_GPU_LIMIT,
    _DEFAULT_MEMORY_LIMIT,
    _DEFAULT_POOL_TREES,
    YtRunner,
    _get_docker_image,
)
from tractoray.ytpath import YtPath


_LOGGER = logging.getLogger(__name__)
_DEFAULT_TIMEOUT = 5.0


class StatusFormat(str, enum.Enum):
    json: str = "json"
    plaintext: str = "plaintext"


def main() -> None:
    log_level = setup_logging()
    parser = argparse.ArgumentParser(
        description="Tractoray CLI tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser(
        "start",
        help="Start Ray cluster on Tracto",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    start_parser.add_argument(
        "--workdir",
        required=True,
        type=str,
        help="Working directory path in YT",
    )
    start_parser.add_argument(
        "--node-count",
        type=int,
        default=1,
        help="Number of nodes in cluster",
    )
    start_parser.add_argument(
        "--docker-image",
        type=str,
        help="Docker image for nodes",
    )
    start_parser.add_argument(
        "--cpu-limit",
        type=int,
        default=_DEFAULT_CPU_LIMIT,
        help="CPU limit per node",
    )
    start_parser.add_argument(
        "--gpu-limit",
        type=int,
        default=_DEFAULT_GPU_LIMIT,
        help="GPU limit per node",
    )
    start_parser.add_argument(
        "--memory-limit",
        type=int,
        default=_DEFAULT_MEMORY_LIMIT,
        help="Memory limit per node in bytes",
    )
    start_parser.add_argument(
        "--pool",
        type=str,
        default=None,
        help="Pool to use",
    )
    start_parser.add_argument(
        "--env-var",
        type=_parse_env_vars,
        action="append",
        help="Set environment variable inside tracto job. Format: KEY=VALUE",
    )
    start_parser.add_argument(
        "--pool-trees",
        nargs="+",
        default=_DEFAULT_POOL_TREES,
        help="Pool trees to use",
    )
    start_parser.add_argument(
        "--ray-head-params",
        default="",
        help="Extra params for `ray start` on head node",
    )
    start_parser.add_argument(
        "--ray-worker-params",
        default="",
        help="Extra params for `ray start` on worker node",
    )
    start_parser.add_argument(
        "--tractoray-source-path",
        help=argparse.SUPPRESS,
        type=Path,
    )
    start_parser.add_argument(
        "--yt-proxy-in-job",
        help=argparse.SUPPRESS,
        default=None,
        type=str,
    )
    start_parser.add_argument(
        "--disable-ariadne",
        action="store_true",
        help="Don't use Ariadne for getting access to Ray cluster. Can only work outside tracto ecosystem",
    )
    status_parser = subparsers.add_parser(
        "status",
        help="Status of Ray cluster",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    status_parser.add_argument(
        "--workdir",
        required=True,
        type=str,
        help="Working directory path in YT",
    )
    status_parser.add_argument(
        "--format",
        required=False,
        default=StatusFormat.plaintext,
        type=StatusFormat,
        help="Output format",
    )
    status_parser.add_argument(
        "--disable-ariadne",
        action="store_true",
        help="Don't use Ariadne for getting access to Ray cluster. Can only work outside tracto ecosystem",
    )

    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop running Ray cluster",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    stop_parser.add_argument(
        "--workdir",
        required=True,
        type=str,
        help="Working directory path in YT",
    )

    args = parser.parse_args()

    yt_client = yt.YtClient(config=yt.default_config.get_config_from_env())

    if args.command == "start":
        print("Starting Ray cluster.")
        docker_image = args.docker_image
        if docker_image is None:
            docker_image = _get_docker_image()
        runner = YtRunner(
            _workdir=args.workdir,
            _node_count=args.node_count,
            _docker_image=docker_image,
            _cpu_limit=args.cpu_limit,
            _gpu_limit=args.gpu_limit,
            _memory_limit=args.memory_limit,
            _pool=args.pool,
            _env_vars=args.env_var or [],
            _pool_trees=args.pool_trees,
            _log_level=log_level,
            _yt_client=yt_client,
            _ray_head_params=args.ray_head_params,
            _ray_worker_params=args.ray_worker_params,
            _tractoray_source_path=args.tractoray_source_path,
            _yt_proxy_in_job=args.yt_proxy_in_job,
        )
        run_info = runner.run()
        print(f"Tracto operation: {run_info.operation_url}")
        while True:
            run_info.check_operation()
            _LOGGER.debug("Waiting for coordination")
            coordination_info = run_info.get_coordination_info()
            if coordination_info:
                print("Ray cluster started.")
                break
            time.sleep(_DEFAULT_TIMEOUT)
        transformer = (
            EmptyTransformer()
            if args.disable_ariadne
            else AriadneTransformer.create(yt_client)
        )
        ray_info = RayInfo(
            _coordination_info=coordination_info,
            _yt_client=yt_client,
            _transformer=transformer,
        )
        print(ray_info.instruction)
    elif args.command == "status":
        coordination_info = CoordinationInfoFactory(
            _yt_client=yt.YtClient(config=yt.default_config.get_config_from_env()),
            _coordinator_path=YtPath(f"{args.workdir}/coordinator"),
        ).get()
        if not coordination_info:
            if args.format == StatusFormat.plaintext:
                print("Ray cluster not found.")
            elif args.format == StatusFormat.json:
                print(json.dumps({"error": "Ray cluster not found."}, indent=4))
            return
        status: OperationState = yt_client.get_operation_state(
            coordination_info.operation_id,
        )
        if not status.is_running():
            if args.format == StatusFormat.plaintext:
                print("Ray cluster is not running.")
            elif args.format == StatusFormat.json:
                print(json.dumps({"error": "Ray cluster is not running."}, indent=4))
            return
        transformer = (
            EmptyTransformer()
            if args.disable_ariadne
            else AriadneTransformer.create(yt_client)
        )
        ray_info = RayInfo(
            _coordination_info=coordination_info,
            _yt_client=yt_client,
            _transformer=transformer,
        )
        if args.format == StatusFormat.plaintext:
            print(f"Ray operation: {ray_info.operation_url}\n")
            print(ray_info.instruction)
        elif args.format == StatusFormat.json:
            print(
                json.dumps(
                    {
                        "operation_url": ray_info.operation_url,
                        "dashboard_url": ray_info.dashboard.address,
                        "cli": {
                            "env": ray_info.dashboard.env,
                        },
                        "client": {
                            "metadata": ray_info.client.metadata,
                            "address": ray_info.client.address,
                        },
                        "head": {
                            "job_shell": ray_info.head_node_job_shell_command,
                            "terminal_url": ray_info.head_node_terminal_url,
                        },
                    },
                    indent=4,
                ),
            )
    elif args.command == "stop":
        coordination_info = CoordinationInfoFactory(
            _yt_client=yt.YtClient(config=yt.default_config.get_config_from_env()),
            _coordinator_path=YtPath(f"{args.workdir}/coordinator"),
        ).get()
        if not coordination_info:
            print("Ray cluster not found.")
            return
        operation_status: OperationState = yt_client.get_operation_state(
            coordination_info.operation_id,
        )
        if not operation_status.is_running():
            print("Ray cluster is not running.")
            return
        yt_client.abort_operation(coordination_info.operation_id)
        print(
            f"Ray cluster stopped, operation {coordination_info.operation_url} has been aborted."
        )


def _parse_env_vars(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"Expected KEY=VALUE format, got: {value}")

    key, val = value.split("=", 1)
    if not key:
        raise argparse.ArgumentTypeError(f"Key cannot be empty in: {value}")

    return key, val


if __name__ == "__main__":
    main()
