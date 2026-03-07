#!/usr/bin/env bash
set -euo pipefail

helm repo add apache-airflow https://airflow.apache.org >/dev/null 2>&1 || true
helm repo update

helm upgrade --install airflow apache-airflow/airflow \
  -n ai-core-pipeline \
  --create-namespace \
  --wait \
  --timeout 10m \
  -f airflow/values.yaml

kubectl -n ai-core-pipeline rollout status deploy/airflow-webserver
kubectl -n ai-core-pipeline rollout status deploy/airflow-scheduler
kubectl -n ai-core-pipeline rollout status deploy/airflow-triggerer
