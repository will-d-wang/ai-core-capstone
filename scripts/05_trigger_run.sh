#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="ai-core-pipeline"
DEFAULT_DAG_ID="daily_ingest"
SCHEDULER="deploy/airflow-scheduler"

usage() {
  cat <<'EOF'
Usage:
  scripts/05_trigger_run.sh trigger <YYYY-MM-DD> [dag_id]
  scripts/05_trigger_run.sh backfill <YYYY-MM-DD> <YYYY-MM-DD> [dag_id]
  scripts/05_trigger_run.sh logs
  scripts/05_trigger_run.sh pods
EOF
}

cmd="${1:-}"
case "$cmd" in
  trigger)
    run_date="${2:-}"
    dag_id="${3:-$DEFAULT_DAG_ID}"
    [[ -n "$run_date" ]] || { usage; exit 1; }
    kubectl -n "$NAMESPACE" exec "$SCHEDULER" -- \
      airflow dags trigger "$dag_id" --logical-date "${run_date}T00:00:00+00:00"
    ;;
  backfill)
    start_date="${2:-}"
    end_date="${3:-}"
    dag_id="${4:-$DEFAULT_DAG_ID}"
    [[ -n "$start_date" && -n "$end_date" ]] || { usage; exit 1; }
    kubectl -n "$NAMESPACE" exec "$SCHEDULER" -- \
      airflow dags backfill "$dag_id" --start-date "$start_date" --end-date "$end_date"
    ;;
  logs)
    kubectl -n "$NAMESPACE" logs deploy/airflow-scheduler --tail=200
    ;;
  pods)
    kubectl -n "$NAMESPACE" get pods -o wide
    ;;
  *)
    usage
    exit 1
    ;;
esac
