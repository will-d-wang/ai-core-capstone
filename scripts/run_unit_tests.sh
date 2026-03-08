#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-local}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIRFLOW_DOCKERFILE="${AIRFLOW_DOCKERFILE:-docker/airflow/Dockerfile}"
AIRFLOW_TEST_IMAGE="${AIRFLOW_TEST_IMAGE:-local/airflow-custom-tests:dev}"

run_local() {
  cd "$ROOT_DIR"
  python -m pytest -q tests
}

run_docker() {
  cd "$ROOT_DIR"
  docker build --target tests -t "$AIRFLOW_TEST_IMAGE" -f "$AIRFLOW_DOCKERFILE" .
  docker run --rm --entrypoint python "$AIRFLOW_TEST_IMAGE" -m pytest -q tests
}

case "$MODE" in
  local)
    run_local
    ;;
  docker)
    run_docker
    ;;
  all)
    run_local
    run_docker
    ;;
  *)
    echo "Usage: $0 [local|docker|all]"
    exit 1
    ;;
esac
