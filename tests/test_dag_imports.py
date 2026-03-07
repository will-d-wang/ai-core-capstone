import importlib

import pytest


def test_dag_modules_import() -> None:
    airflow = pytest.importorskip("airflow")
    if not hasattr(airflow, "DAG"):
        pytest.skip("Apache Airflow is not fully installed in this environment")
    importlib.import_module("dags.daily_ingest")
    importlib.import_module("dags.daily_feature_build")
