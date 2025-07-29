# Tractoray

The tool for running [Ray](https://www.ray.io/) clusters on [Tracto.ai](https://tracto.ai/). Allows you to easily deploy and manage Ray clusters within Tracto.ai infrastructure.

## Features

- Launch Ray clusters with configurable resources.
- Support native ray dashboard and ray client.
- Support Ray Debugger.
- Flexible Docker image configuration.

To see all the configuration options for Ray, please check the output of the `tractoratay start --help` command.

## Installation

Install `tractoray` with Ray CLI and all required dependencies:
```bash
pip install -U "tractoray[ray]"
```

## Usage

### Basic Commands

To use `tractoray`, you need to specify the working directory, for example your homedir `//home/<login>/tractoray`.

Start a cluster:
```bash
tractoray start --workdir //your/cypress/path --node-count 2
```

An output of the command contains an instruction to connect to the cluster.

Check the cluster status:
```bash
tractoray status --workdir //your/yt/path
```

Also JSON format is supported:
```bash
tractoray status --workdir //your/cypress/path --format json
```

Stop the cluster:
```bash
tractoray stop --workdir //your/cypress/path
```

For detailed information about task submission, log reading, and other operations, please check the `ray status` command output.

### Using Custom Docker Images

You have two options for Docker images:

1. Use the default image as base (recommended):
   ```dockerfile
   FROM cr.eu-north1.nebius.cloud/e00faee7vas5hpsh3s/tractoray/default:2025-06-12-16-59-42-9a2ce5611
   
   # Add your dependencies
   RUN pip install your-package
   ```

2. Build from scratch:
   - Install `tractoray` via pip
   - Use the same version as in your local environment and install all necessary dependencies for CUDA and Infiniband.
   ```dockerfile
   FROM python:3.12
   
   RUN pip install tractoray==<your-local-version>
   # Add other dependencies
   ```

The default image includes all necessary dependencies and configurations to run Ray clusters for ML workloads. Using it as a base image is recommended to ensure compatibility.

### Connect to the Ray Head Node terminal

Connect to the Ray head node terminal via the [yt run-job-shell](https://ytsaurus.tech/docs/en/user-guide/problems/jobshell-and-slowjobs) command or the web terminal in the UI. The `tractoratay status` command shows all necessary instructions and links.

### Ray Debugging

Currently, only the [legacy Ray debugger](https://docs.ray.io/en/latest/ray-observability/user-guides/debug-apps/ray-debugging.html) is supported.

To use ray debugger on Tracto.ai:
1. Start your Ray cluster with `RAY_DEBUG=legacy` environment variable and the `--ray-debugger-external` option: `tractoray start --workdir //your/cypress/path --ray-head-params="--ray-debugger-external" --ray-worker-params="--ray-debugger-external" --env-var "RAY_DEBUG=legacy"`
2. Connect to the Ray head node terminal using `yt run-job-shell` or web UI (instructions and necessary links can be found in the output of `ray start` and `ray status`).
3. Run `ray debug` in the terminal on the head node to start the Ray Debugger.

You can read more about debugging Ray tasks in the official [Ray documentation](https://docs.ray.io/en/latest/ray-observability/user-guides/debug-apps/ray-debugging.html).

## Environment Variables

- `YT_LOG_LEVEL`: Set logging level

## Limitations

- Some Ray CLI options, like `ray status`, may not work properly on a laptop due to Ray authentication constraints. Use the Ray dashboard and the Ray SDK, or run Ray CLI on the head node instead.
- Ray Serve is not supported.
- Observability features are disabled by default. You can enable and configure them in your custom image.
- Only legacy Ray Debugger is supported.
