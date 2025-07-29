#!/usr/bin/env bash

set -x

_CURRENT_DOCKER_TAG="2025-03-07-01-05-14-2a80510f5"
IMAGE_GENERIC="cr.eu-north1.nebius.cloud/e00faee7vas5hpsh3s/chiffa/tractoray/tests:$_CURRENT_DOCKER_TAG"

PATH_GENERIC="/src/tests"

TEST_TYPE="${1:-all}"

IMAGES=()
TEST_PATHS=()

case "$TEST_TYPE" in
  "generic")
    IMAGES=("$IMAGE_GENERIC")
    TEST_PATHS=("$PATH_GENERIC")
    ;;
  "all")
    IMAGES=("$IMAGE_GENERIC")
    TEST_PATHS=("$PATH_GENERIC")
    ;;
  *)
    echo "Invalid test type: $TEST_TYPE."
    exit 1
    ;;
esac

run_tests() {
  local image=$1
  local test_path=$2
  docker run -it \
    --mount type=bind,source=.,target=/src \
    --network=host \
    -e YT_MODE=external \
    -e YT_PROXY="${YT_PROXY}" \
    -e YT_TOKEN="${YT_TOKEN}" \
    -e YT_LOG_LEVEL="${YT_LOG_LEVEL}" \
    -e PYTHONPATH="/src:$PYTHONPATH" \
    -e PYTHONDONTWRITEBYTECODE=1 \
    "$image" \
    pytest "$test_path" "${@:3}"
}

for i in "${!IMAGES[@]}"; do
  if [[ "$2" == -* ]]; then
    TEST_NAME=""
    TEST_ARGS=${@:2}
  else
    TEST_NAME=$2
    TEST_ARGS=${@:3}
  fi
  run_tests "${IMAGES[$i]}" "${TEST_PATHS[$i]}/$TEST_NAME" $TEST_ARGS
done
