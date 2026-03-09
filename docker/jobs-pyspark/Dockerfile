FROM python:3.12-slim AS deps

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY jobs/ /app/jobs/
COPY airflow/ /app/airflow/
RUN pip install --no-cache-dir -e ".[jobs-spark]"

ENV PYTHONPATH=/app

FROM deps AS tests
RUN pip install --no-cache-dir -e ".[dev]"

FROM deps AS runtime
ENTRYPOINT ["python", "-m", "jobs.pyspark.ingest_job"]
