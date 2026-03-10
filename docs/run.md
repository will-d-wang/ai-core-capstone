# Run

## Start Local Cluster

```bash
scripts/00_minikube_up.sh
minikube status -p ai-core-etl
```

## Build Images

```bash
scripts/build_images.sh
```

This builds:

- `local/spark-job:dev`
- `local/airflow-custom:dev` (installs Airflow dependencies from `pyproject.toml` and runs unit tests in a Docker build stage)

## Configure Credentials

For demo usage, defaults exist in scripts, but avoid committing real secrets.

```bash
export POSTGRES_USER='airflow'
export POSTGRES_PASSWORD='change-me-postgres'
export POSTGRES_DB='airflow'
export MINIO_ROOT_USER='minioadmin'
export MINIO_ROOT_PASSWORD='change-me-minio'
export AIRFLOW_ADMIN_USERNAME='admin'
export AIRFLOW_ADMIN_PASSWORD='change-me-airflow-admin'
export AIRFLOW_ADMIN_EMAIL='admin@example.com'
export AIRFLOW_ADMIN_FIRST_NAME='Admin'
export AIRFLOW_ADMIN_LAST_NAME='User'
```

## Deploy Infrastructure

```bash
scripts/01_deploy_infra.sh
```

`scripts/01_deploy_infra.sh` runs a single Terraform apply from `infra/terraform` and:

- Creates `pipeline-secrets` from `POSTGRES_*` and `MINIO_*` env vars
- Creates `airflow-metadata-secret` from DB env vars
- Deploys Postgres and MinIO
- Installs Airflow via Helm
- Optionally runs `scripts/bootstrap_env.sh` after apply

`scripts/bootstrap_env.sh`:

- Waits for Postgres, MinIO, and Airflow scheduler rollout
- Runs the seed-data job
- Configures local access and verifies MinIO API health

Set `SKIP_BOOTSTRAP=true` to run Terraform apply without bootstrap steps.

Before running, set your DAG git repo in `airflow/helm-values.yaml`:

- Replace `https://github.com/<YOUR_GITHUB>/<YOUR_REPO>.git`

## Access Services

- Airflow: `http://airflow.local` (`$AIRFLOW_ADMIN_USERNAME` / `$AIRFLOW_ADMIN_PASSWORD`)
- MinIO console: `http://minio-console.local` (`$MINIO_ROOT_USER` / `$MINIO_ROOT_PASSWORD`)

## Trigger DAGs

```bash
scripts/02_trigger_run.sh trigger 2026-03-06 daily_ingest
scripts/02_trigger_run.sh trigger 2026-03-06 daily_feature_build
scripts/02_trigger_run.sh backfill 2026-03-06 2026-03-07 daily_ingest
```
