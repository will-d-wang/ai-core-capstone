#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-ai-core-etl}"

eval "$(minikube -p "$PROFILE" docker-env)"

if ! docker version >/tmp/docker-version.out 2>/tmp/docker-version.err; then
  if grep -q "Maximum supported API version is" /tmp/docker-version.err; then
    max_api_version="$(sed -n 's/.*Maximum supported API version is \([0-9.]\+\).*/\1/p' /tmp/docker-version.err | head -n1)"
    if [[ -n "${max_api_version}" ]]; then
      export DOCKER_API_VERSION="$max_api_version"
      echo "Using Docker API compatibility mode: ${DOCKER_API_VERSION}"
    fi
  fi
fi

docker build -t local/spark-job:dev -f docker/jobs-pyspark/Dockerfile .
docker build -t local/airflow-custom:dev -f docker/airflow/Dockerfile .
