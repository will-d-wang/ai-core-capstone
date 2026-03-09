# AI Core ETL Demo (Airflow + Spark + Kubernetes)

This project demonstrates a daily ETL + feature build pipeline using Airflow orchestration, PySpark transforms, and Kubernetes task isolation.

## Layout

- `airflow/dags/daily_ingest.py`
- `airflow/dags/daily_feature_build.py`
- `jobs/pyspark/ingest_job.py`
- `jobs/pyspark/feature_job.py`
- `airflow/helm-values.yaml`
- `airflow/requirements.txt`
- `airflow/tests/test_dag_imports.py`
- `jobs/tests/test_feature_job.py`

## Prerequisites

- Docker
- Minikube
- kubectl
- Helm 3
- uv
- Python 3.11+

## Local Dev (uv)

Create separate local environments for each runtime profile:

```bash
# Airflow runtime + dev tools
uv venv .venv-airflow
source .venv-airflow/bin/activate
uv pip install -e ".[airflow,dev]"
deactivate

# Spark jobs runtime + dev tools
uv venv .venv-jobs-spark
source .venv-jobs-spark/bin/activate
uv pip install -e ".[jobs-spark,dev]"
deactivate
```

Run tests and tooling from the matching environment:

```bash
# Airflow tests
source .venv-airflow/bin/activate
pytest airflow/tests
deactivate

# Spark jobs tests
source .venv-jobs-spark/bin/activate
pytest jobs/tests
deactivate

# Lint and type-check (either env with `dev` installed)
source .venv-jobs-spark/bin/activate
ruff check .
mypy
deactivate
```

## Run

1. Start Minikube profile for this project:

```bash
scripts/00_minikube_up.sh
# Optional sanity check (explicit profile):
minikube status -p ai-core-etl
```

2. Build runtime images into Minikube Docker daemon:

```bash
scripts/build_images.sh
```

This builds:
- `local/spark-job:dev`
- `local/airflow-custom:dev` (installs `airflow/requirements.txt` and runs unit tests in a Docker build stage)

3. Set credentials via environment variables (recommended).  
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

4. Deploy infra (namespace, secrets/configmap, Postgres, MinIO):

```bash
scripts/01_deploy_infra.sh
```

`scripts/01_deploy_infra.sh` creates/updates:
- `pipeline-secrets` from `POSTGRES_*` and `MINIO_*` env vars
- `airflow-metadata-secret` from DB env vars (used by Airflow as metadata connection)

5. Set your DAG git repo in `airflow/helm-values.yaml`:

- Replace `https://github.com/<YOUR_GITHUB>/<YOUR_REPO>.git`.

6. Install Airflow chart:

```bash
scripts/02_install_airflow.sh
```

`scripts/02_install_airflow.sh` reads Airflow admin user values from `AIRFLOW_ADMIN_*` env vars.
Airflow uses the custom image configured in `airflow/helm-values.yaml` (`local/airflow-custom:dev`).

7. Seed sample raw data:

```bash
scripts/03_seed_data.sh
```

8. Port-forward UIs:

```bash
scripts/04_port_forward.sh
```

- Airflow: `http://localhost:8080` (`$AIRFLOW_ADMIN_USERNAME` / `$AIRFLOW_ADMIN_PASSWORD`)
- MinIO console: `http://localhost:9001` (`$MINIO_ROOT_USER` / `$MINIO_ROOT_PASSWORD`)

## Trigger DAGs

```bash
scripts/05_trigger_run.sh trigger 2026-03-06 daily_ingest
scripts/05_trigger_run.sh trigger 2026-03-06 daily_feature_build
scripts/05_trigger_run.sh backfill 2026-03-06 2026-03-07 daily_ingest
```

## Tests

```bash
scripts/run_unit_tests.sh local
# or:
scripts/run_unit_tests.sh docker
```

## Debugging

```bash
scripts/05_trigger_run.sh pods
scripts/05_trigger_run.sh logs
kubectl -n ai-core-pipeline logs <spark-pod-name>
kubectl -n ai-core-pipeline describe pod <spark-pod-name>
```
