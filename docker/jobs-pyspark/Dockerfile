FROM python:3.12-slim AS deps

WORKDIR /app

COPY jobs/requirements-spark.txt /app/jobs/requirements-spark.txt
RUN pip install --no-cache-dir -r /app/jobs/requirements-spark.txt
COPY jobs/ /app/jobs/

ENV PYTHONPATH=/app

FROM deps AS tests
RUN pip install --no-cache-dir pytest

FROM deps AS runtime
ENTRYPOINT ["python", "-m", "jobs.pyspark.ingest_job"]
