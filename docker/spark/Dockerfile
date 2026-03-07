FROM python:3.11-slim

WORKDIR /app

COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/spark.txt
COPY jobs/ /app/jobs/

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "jobs.pyspark.ingest_job"]
