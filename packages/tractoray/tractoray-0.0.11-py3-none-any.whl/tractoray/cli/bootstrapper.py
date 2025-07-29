import argparse
import logging
import os

import yt.wrapper as yt

from tractoray.internal.bootstrap import (
    BootstrapperHead,
    BootstrapperNode,
)
from tractoray.internal.logs import setup_logging
from tractoray.ytpath import YtPath


_LOGGER = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    _LOGGER.info("Starting bootstrapper")
    parser = argparse.ArgumentParser(description="Bootstrap Ray in YT operation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    head_parser = subparsers.add_parser("head", help="Run head node")
    node_parser = subparsers.add_parser("node", help="Run worker node")

    for subparser in (head_parser, node_parser):
        subparser.add_argument(
            "--workdir",
            required=True,
            type=str,
            help="Working directory path in YT",
        )
        subparser.add_argument(
            "--proxy",
            required=True,
            type=str,
            help="YT proxy URL",
        )
        subparser.add_argument(
            "--cpu-limit",
            required=True,
            type=int,
            help="CPU limit per node",
        )
        subparser.add_argument(
            "--node-count",
            required=True,
            type=int,
            help="Number of nodes in cluster",
        )
        subparser.add_argument(
            "--ray-params",
            required=True,
            type=str,
            help="Extra params for `ray start` command",
        )

    args = parser.parse_args()
    yt_client = yt.YtClient(
        proxy=args.proxy,
        token=os.environ["YT_SECURE_VAULT_USER_YT_TOKEN"],
        config=yt.default_config.get_config_from_env(),
    )
    if args.command == "head":
        BootstrapperHead(
            _yt_client=yt_client,
            _workdir=YtPath(args.workdir),
            _cpu_limit=args.cpu_limit,
            _node_count=args.node_count,
            _node_index=int(os.environ["YT_JOB_COOKIE"]),
            _operation_id=os.environ["YT_OPERATION_ID"],
            _job_id=os.environ["YT_JOB_ID"],
            _head_port=int(os.environ["YT_PORT_0"]),
            _head_job_id=str(os.environ["YT_JOB_ID"]),
            _dashboard_port=int(os.environ["YT_PORT_1"]),
            _dashboard_agent_listen_port=int(os.environ["YT_PORT_2"]),
            _public_dashboard_port=int(os.environ["YT_PORT_3"]),
            _client_port=int(os.environ["YT_PORT_4"]),
            _runtime_env_agent_port=int(os.environ["YT_PORT_5"]),
            _ray_params=args.ray_params,
        ).run()
    else:
        BootstrapperNode(
            _yt_client=yt_client,
            _workdir=YtPath(args.workdir),
            _cpu_limit=args.cpu_limit,
            _node_count=args.node_count,
            _node_index=int(os.environ["YT_JOB_COOKIE"]) + 1,
            _operation_id=os.environ["YT_OPERATION_ID"],
            _job_id=os.environ["YT_JOB_ID"],
            _runtime_env_agent_port=int(os.environ["YT_PORT_0"]),
            _ray_params=args.ray_params,
        ).run()


if __name__ == "__main__":
    main()
