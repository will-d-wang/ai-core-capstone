from datetime import datetime, timedelta
import os

from airflow import DAG
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
    dag_id="daily_feature_build",
    start_date=datetime(2026, 3, 1),
    schedule="@daily",
    catchup=True,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    tags=["ai-core", "feature"],
) as dag:
    run_date = "{{ ds }}"

    KubernetesPodOperator(
        task_id="run_feature_build",
        namespace=NAMESPACE,
        image=SPARK_IMAGE,
        image_pull_policy="IfNotPresent",
        name="daily-feature-build",
        arguments=["--run_date", run_date],
        cmds=["python", "-m", "jobs.pyspark.feature_job"],
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
    )
