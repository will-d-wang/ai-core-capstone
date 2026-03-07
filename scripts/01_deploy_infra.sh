#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -n ai-core-pipeline -f infra/k8s/secrets.yaml
kubectl apply -n ai-core-pipeline -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/minio.yaml

kubectl -n ai-core-pipeline rollout status statefulset/postgres
kubectl -n ai-core-pipeline rollout status deploy/minio
