# Architecture

This document describes the system using C4-style Mermaid diagrams. The diagrams reflect the current local deployment model in this repository: Airflow on Kubernetes, Spark jobs launched as pods, MinIO as S3-compatible storage, and Postgres for Airflow metadata.

## System Context

```mermaid
C4Context
title Airflow Spark ETL System Context

Person(operator, "Developer / Operator", "Builds images, deploys infrastructure, triggers DAGs, and inspects runs")
System_Ext(git_repo, "Git Repository", "Hosts the Airflow DAG source used by git-sync")
System_Ext(browser, "Browser", "Used to access Airflow and MinIO UIs")

System_Boundary(etl_boundary, "Capstone Airflow Spark K8s ETL") {
    System(etl_system, "ETL Platform", "Airflow, Spark, MinIO, Postgres, Kubernetes", "Ingests raw events, builds curated data, and computes daily features")
}

Rel(operator, etl_system, "Deploys, runs, and operates")
Rel(operator, browser, "Uses")
Rel(browser, etl_system, "Accesses UI endpoints")
Rel(git_repo, etl_system, "Provides DAG source")
```

Notes:

- The primary actor is an engineer or operator, not an end-user application.
- The repo supplies orchestration code through Airflow `git-sync`; Spark job code is baked into the runtime image.
- The system is modeled as one deployable platform for the context view, even though it contains multiple containers internally.

## Container View

```mermaid
C4Container
title Airflow Spark ETL Container View

Person(operator, "Developer / Operator", "Builds images, deploys infra, triggers DAGs")
System_Ext(git_repo, "Git Repository", "Source of `airflow/dags`")

System_Boundary(k8s, "Minikube / Kubernetes Cluster") {
    Container(airflow, "Airflow", "Helm chart + Python", "Schedules DAGs and launches Kubernetes pods for ETL work")
    ContainerDb(postgres, "Postgres", "PostgreSQL", "Stores Airflow metadata")
    Container(minio, "MinIO", "S3-compatible object store", "Stores raw, curated, and feature datasets")
    Container(seed_job, "Seed Data Job", "Kubernetes Job + MinIO client", "Creates the bucket and uploads demo raw data")
    Container(spark_pods, "Spark Job Pods", "Python + PySpark", "Run ingest and feature build entrypoints")
}

Rel(operator, airflow, "Uses via UI and CLI workflows")
Rel(operator, seed_job, "Runs during bootstrap")
Rel(git_repo, airflow, "Syncs DAG definitions", "git-sync")
Rel(airflow, postgres, "Reads and writes metadata", "SQL")
Rel(airflow, spark_pods, "Starts ETL jobs", "KubernetesPodOperator")
Rel(seed_job, minio, "Creates bucket and uploads raw events", "S3 API")
Rel(spark_pods, minio, "Reads raw/curated data and writes outputs", "S3A")
```

Notes:

- Airflow is the control plane; Spark pods are short-lived execution containers.
- Postgres is only used for Airflow metadata in this repo, not for pipeline business data.
- MinIO stands in for S3 in local development and stores all ETL datasets.
- The seed job is operational bootstrap glue, not part of the steady-state daily pipeline.

## Component View

```mermaid
C4Component
title ETL Pipeline Component View

Container_Boundary(airflow_runtime, "Airflow + Spark Runtime") {
    Component(dag_ingest, "daily_ingest DAG", "Airflow DAG", "Discovers tenants and fans out ingest executions")
    Component(dag_feature, "daily_feature_build DAG", "Airflow DAG", "Schedules the daily feature aggregation run")
    Component(ingest_job, "Ingest Job", "PySpark module", "Validates schema, filters by date, deduplicates events, writes curated parquet")
    Component(feature_job, "Feature Job", "PySpark module", "Aggregates curated events into daily tenant features")
}

ComponentDb(raw_data, "Raw Dataset", "MinIO / S3 path", "`raw/dt=.../tenant_id=...` JSON events")
ComponentDb(curated_data, "Curated Events Dataset", "MinIO / S3 path", "`curated/events/` parquet")
ComponentDb(feature_data, "Feature Dataset", "MinIO / S3 path", "`curated/features/` parquet")

Rel(dag_ingest, ingest_job, "Launches", "KubernetesPodOperator")
Rel(dag_feature, feature_job, "Launches", "KubernetesPodOperator")
Rel(ingest_job, raw_data, "Reads")
Rel(ingest_job, curated_data, "Writes")
Rel(feature_job, curated_data, "Reads")
Rel(feature_job, feature_data, "Writes")
Rel(dag_feature, curated_data, "Depends on data produced in prior ingest runs", "implicit data dependency")
```

Notes:

- The DAGs are intentionally thin and orchestration-focused; transformation logic lives in the PySpark jobs.
- `daily_ingest` fans out by tenant, while `daily_feature_build` is a single daily aggregation step.
- The dependency between ingest and feature build is currently data-driven rather than enforced as one composed DAG.
- The component view models storage paths as components because the pipeline contract is path-oriented.

## Modeling Notes

- These are C4-style diagrams rendered with Mermaid syntax, not PlantUML C4 macros.
- The container/component boundaries are logical and optimized for explanation, not a literal one-to-one mapping to every pod created at runtime.
- If the repo later adds a shared `src/` package, that would fit naturally into the component view as shared library code used by the DAG and job entrypoints.
