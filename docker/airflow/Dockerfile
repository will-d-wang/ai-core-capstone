FROM apache/airflow:3.1.7 AS deps

WORKDIR /opt/airflow
USER airflow
COPY pyproject.toml README.md /opt/airflow/
COPY airflow/ /opt/airflow/airflow/
RUN pip install --no-cache-dir -e ".[airflow]"
ENV PYTHONPATH=/opt/airflow

FROM deps AS tests
RUN pip install --no-cache-dir -e ".[dev]"

FROM deps AS runtime
