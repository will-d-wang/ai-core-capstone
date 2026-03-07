#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-ai-core-etl}"

minikube start -p "$PROFILE" --cpus=6 --memory=12288 --disk-size=40g
minikube addons enable ingress -p "$PROFILE"
minikube addons enable metrics-server -p "$PROFILE"

# So we can build images directly into minikube docker daemon
eval "$(minikube -p "$PROFILE" docker-env)"

# Keep kubectl context aligned with this profile
kubectl config use-context "$PROFILE" >/dev/null
