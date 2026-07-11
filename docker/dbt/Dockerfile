FROM python:3.11-slim

WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir dbt-postgres psycopg2-binary pyyaml
COPY dbt /workspace/dbt
