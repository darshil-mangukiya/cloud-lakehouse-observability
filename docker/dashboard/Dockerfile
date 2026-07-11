FROM python:3.11-slim

WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir pandas streamlit
COPY . /workspace
