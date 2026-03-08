from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.sdk import task
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

NAMESPACE = "ai-core-pipeline"
SPARK_IMAGE = os.environ.get("SPARK_IMAGE", "local/spark-job:dev")

DEFAULT_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}

with DAG(
    dag_id="daily_ingest",
    start_date=datetime(2026, 3, 1),
    schedule="@daily",
    catchup=True,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    tags=["ai-core", "ingest"],
) as dag:

    @task
    def discover_tenants() -> list[str]:
        return ["T1", "T2"]

    @task
    def build_ingest_args(run_date: str, tenants: list[str]) -> list[list[str]]:
        return [["--run_date", run_date, "--tenant_id", tenant] for tenant in tenants]

    run_date = "{{ ds }}"
    tenants = discover_tenants()
    ingest_args = build_ingest_args(run_date, tenants)

    KubernetesPodOperator.partial(
        task_id="run_ingest",
        namespace=NAMESPACE,
        image=SPARK_IMAGE,
        image_pull_policy="IfNotPresent",
        name="daily-ingest",
        cmds=["python", "-m", "jobs.pyspark.ingest_job"],
        env_from=[
            k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name="pipeline-config")),
            k8s.V1EnvFromSource(secret_ref=k8s.V1SecretEnvSource(name="pipeline-secrets")),
        ],
        container_resources=k8s.V1ResourceRequirements(
            requests={"cpu": "500m", "memory": "1Gi"},
            limits={"cpu": "2", "memory": "4Gi"},
        ),
        get_logs=True,
        log_events_on_failure=True,
        startup_timeout_seconds=600,
        execution_timeout=timedelta(minutes=45),
        on_finish_action="delete_pod",
    ).expand(arguments=ingest_args)
