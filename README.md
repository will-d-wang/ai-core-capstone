# AI Core ETL Demo (Airflow + Spark + Kubernetes)

This project demonstrates a daily ETL + feature build pipeline using Airflow orchestration, PySpark transforms, and Kubernetes task isolation.

## Layout

- `dags/daily_ingest.py`
- `dags/daily_feature_build.py`
- `jobs/pyspark/ingest_job.py`
- `jobs/pyspark/feature_job.py`
- `airflow/values.yaml`
- `airflow/requirements.txt`
- `tests/test_dag_imports.py`
- `tests/test_feature_job.py`

## Prerequisites

- Docker
- Minikube
- kubectl
- Helm 3
- Python 3.11+

## Run

1. Start Minikube profile for this project:

```bash
scripts/00_minikube_up.sh
```

2. Build Spark image into Minikube Docker daemon:

```bash
scripts/build_images.sh
```

3. Deploy infra (namespace, secrets/configmap, Postgres, MinIO):

```bash
scripts/01_deploy_infra.sh
```

4. Set your DAG git repo in `airflow/values.yaml`:

- Replace `https://github.com/<YOUR_GITHUB>/<YOUR_REPO>.git`.

5. Install Airflow chart:

```bash
scripts/02_install_airflow.sh
```

6. Seed sample raw data:

```bash
scripts/03_seed_data.sh
```

7. Port-forward UIs:

```bash
scripts/04_port_forward.sh
```

- Airflow: `http://localhost:8080` (`admin/admin`)
- MinIO console: `http://localhost:9001` (`minioadmin/minioadmin123`)

## Trigger DAGs

```bash
scripts/05_trigger_run.sh trigger 2026-03-06 daily_ingest
scripts/05_trigger_run.sh trigger 2026-03-06 daily_feature_build
scripts/05_trigger_run.sh backfill 2026-03-06 2026-03-07 daily_ingest
```

## Tests

```bash
pytest -q tests
```

## Debugging

```bash
scripts/05_trigger_run.sh pods
scripts/05_trigger_run.sh logs
kubectl -n ai-core-pipeline logs <spark-pod-name>
kubectl -n ai-core-pipeline describe pod <spark-pod-name>
```
