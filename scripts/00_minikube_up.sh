#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-ai-core-etl}"
NODE_TIMEOUT="${NODE_TIMEOUT:-180s}"
METRICS_TIMEOUT_SECONDS="${METRICS_TIMEOUT_SECONDS:-180}"
METRICS_POLL_INTERVAL_SECONDS="${METRICS_POLL_INTERVAL_SECONDS:-5}"

minikube start -p "$PROFILE" --cpus=6 --memory=12288 --disk-size=40g
minikube addons enable ingress -p "$PROFILE"
minikube addons enable metrics-server -p "$PROFILE"

# Keep minikube CLI and kubectl aligned with this profile/context.
minikube profile "$PROFILE" >/dev/null

# So we can build images directly into minikube docker daemon
eval "$(minikube -p "$PROFILE" docker-env)"

kubectl config use-context "$PROFILE" >/dev/null

echo "Waiting for node readiness..."
kubectl wait --for=condition=Ready node --all --timeout="$NODE_TIMEOUT"

echo "Waiting for metrics-server API..."
end=$((SECONDS + METRICS_TIMEOUT_SECONDS))
until kubectl get --raw /apis/metrics.k8s.io/v1beta1 >/dev/null 2>&1; do
  if (( SECONDS >= end )); then
    echo "Timed out waiting for metrics API after ${METRICS_TIMEOUT_SECONDS}s"
    kubectl -n kube-system get pods -l k8s-app=metrics-server -o wide || true
    exit 1
  fi
  sleep "$METRICS_POLL_INTERVAL_SECONDS"
done

echo "Minikube status:"
minikube status -p "$PROFILE"

echo "Kubernetes nodes:"
kubectl get nodes

echo "Metrics API resources:"
kubectl api-resources --api-group=metrics.k8s.io
