#!/usr/bin/env bash

set -x
if [ -z "$CURRENT_DATE" ]; then
  CURRENT_DATE=$(date '+%Y-%m-%d-%H-%M-%S')
fi

if [ -z "$COMMIT_ID" ]; then
  COMMIT_ID=$(git rev-parse --short HEAD)
fi


ALL_BAKE_FILES=(
    build.hcl
    vars.hcl
)

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

FILE_ARGS=()
for BAKE_FILE in "${ALL_BAKE_FILES[@]}"
do
  FILE_ARGS+=(--file "${SCRIPT_DIR}/docker/${BAKE_FILE}")
done

export PROJECT_ROOT="${SCRIPT_DIR}"
export DOCKER_TAG="${CURRENT_DATE}-${COMMIT_ID}"

exec docker buildx bake "${FILE_ARGS[@]}" "$@"

