# ETL Demo Alignment Notes

## Airflow reliability
- DAGs: `daily_ingest`, `daily_feature_build`
- Retries + backoff: `retries=3`, exponential backoff, max retry delay
- Catchup/backfill: `catchup=True` with daily schedule
- Task isolation: Spark runs in Kubernetes pods via `KubernetesPodOperator`

## Spark correctness and performance
- Ingest job uses explicit input schema and dedupe window by `(tenant_id, event_id)`
- Output partitioning by `dt` and `tenant_id`
- Configurable shuffle partitions (`--shuffle_partitions`)
- Feature job aggregates per-day/per-tenant metrics from curated events

## Kubernetes operations
- Airflow installed with Helm from `airflow/values.yaml`
- Separation of concerns:
  - config in `infra/k8s/configmap.yaml`
  - secrets in `infra/k8s/secrets.yaml`
- Ops helpers:
  - `scripts/05_trigger_run.sh pods`
  - `scripts/05_trigger_run.sh logs`

## AWS mapping
- MinIO -> S3
- Postgres -> RDS for PostgreSQL
- Minikube/K8s -> EKS
- K8s secrets -> Secrets Manager/SSM
- Static keys in demo -> IRSA in production
