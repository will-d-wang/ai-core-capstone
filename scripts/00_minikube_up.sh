#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-ai-core-etl}"
NODE_TIMEOUT="${NODE_TIMEOUT:-180s}"
METRICS_TIMEOUT_SECONDS="${METRICS_TIMEOUT_SECONDS:-180}"
METRICS_POLL_INTERVAL_SECONDS="${METRICS_POLL_INTERVAL_SECONDS:-5}"
MINIKUBE_CPUS="${MINIKUBE_CPUS:-6}"
MINIKUBE_MEMORY_MB="${MINIKUBE_MEMORY_MB:-12288}"
MINIKUBE_DISK_SIZE="${MINIKUBE_DISK_SIZE:-40g}"

get_minikube_status() {
  if minikube status -p "$PROFILE" --format='{{.Host}} {{.Kubelet}} {{.APIServer}}' >/dev/null 2>&1; then
    minikube status -p "$PROFILE" --format='{{.Host}} {{.Kubelet}} {{.APIServer}}'
    return
  fi

  echo ""
}

start_minikube_if_needed() {
  local status
  status="$(get_minikube_status)"

  if [[ "$status" == "Running Running Running" ]]; then
    echo "Minikube profile '$PROFILE' is already running; skipping start."
    return
  fi

  echo "Starting minikube profile '$PROFILE'..."
  minikube start -p "$PROFILE" \
    --cpus="$MINIKUBE_CPUS" \
    --memory="$MINIKUBE_MEMORY_MB" \
    --disk-size="$MINIKUBE_DISK_SIZE"
  minikube addons enable ingress -p "$PROFILE"
  minikube addons enable metrics-server -p "$PROFILE"
}

configure_minikube_context() {
  minikube profile "$PROFILE" >/dev/null
  eval "$(minikube -p "$PROFILE" docker-env)"
  kubectl config use-context "$PROFILE" >/dev/null
}

wait_for_nodes_ready() {
  echo "Waiting for node readiness..."
  kubectl wait --for=condition=Ready node --all --timeout="$NODE_TIMEOUT"
}

wait_for_metrics_api() {
  local end
  end=$((SECONDS + METRICS_TIMEOUT_SECONDS))

  echo "Waiting for metrics-server API..."
  until kubectl get --raw /apis/metrics.k8s.io/v1beta1 >/dev/null 2>&1; do
    if (( SECONDS >= end )); then
      echo "Timed out waiting for metrics API after ${METRICS_TIMEOUT_SECONDS}s"
      kubectl -n kube-system get pods -l k8s-app=metrics-server -o wide || true
      exit 1
    fi
    sleep "$METRICS_POLL_INTERVAL_SECONDS"
  done
}

print_cluster_diagnostics() {
  echo "Minikube status:"
  minikube status -p "$PROFILE"

  echo "Kubernetes nodes:"
  kubectl get nodes

  echo "Metrics API resources:"
  kubectl api-resources --api-group=metrics.k8s.io

  echo "Ingress controller image:"
  kubectl -n ingress-nginx get deploy ingress-nginx-controller \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
  echo
}

main() {
  start_minikube_if_needed
  configure_minikube_context
  wait_for_nodes_ready
  wait_for_metrics_api
  print_cluster_diagnostics
}

main "$@"
