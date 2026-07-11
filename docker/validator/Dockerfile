FROM python:3.11-slim

WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir pandas great_expectations pyyaml python-dotenv
COPY . /workspace
