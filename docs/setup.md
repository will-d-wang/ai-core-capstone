# Setup

## Prerequisites

- Docker
- Minikube
- kubectl
- Helm 3
- Terraform
- uv
- Python 3.11+

## Local Dev

Use a single local environment with both runtime profiles installed:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[airflow,jobs-spark,dev]"
```

Run tests and tooling from the same environment:

```bash
source .venv/bin/activate
pytest airflow/tests
pytest jobs/tests
ruff check .
mypy
```
