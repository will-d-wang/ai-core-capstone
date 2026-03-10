# Production Demo Alignment

This document summarizes how the local demo maps to common production-oriented ETL expectations across orchestration, Spark execution, Kubernetes operations, and cloud architecture.

## Airflow Reliability

- DAGs: `daily_ingest` and `daily_feature_build`
- Retry policy: `retries=3` with exponential backoff and a maximum retry delay
- Scheduling model: daily schedule with `catchup=True` for backfill support
- Task isolation: Spark work runs in separate Kubernetes pods through `KubernetesPodOperator`

## Spark Correctness And Performance

- The ingest job uses an explicit input schema for raw JSON events
- Event deduplication is performed by `(tenant_id, event_id)` with a latest-record window
- Outputs are partitioned by `dt` and `tenant_id`
- Shuffle parallelism is configurable with `--shuffle_partitions`
- The feature job aggregates curated events into daily per-tenant metrics

## Kubernetes Operations

- Airflow is installed with Helm using `airflow/helm-values.yaml`
- Platform infrastructure is separated from application deployment logic
- Terraform platform resources live under `infra/terraform/modules/platform`
- Bootstrap and post-apply helpers live under `scripts/libs/deploy_infra`
- Operational checks are exposed through `scripts/02_trigger_run.sh pods` and `scripts/02_trigger_run.sh logs`

## AWS Mapping

- MinIO maps to Amazon S3
- Postgres maps to Amazon RDS for PostgreSQL
- Minikube and local Kubernetes map to Amazon EKS
- Kubernetes secrets map to AWS Secrets Manager or SSM Parameter Store
- Static demo credentials should be replaced with IRSA-based access in production
