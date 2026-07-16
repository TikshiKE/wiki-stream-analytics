# Build from repository root: docker build -f services/dbt-runner/Dockerfile .
FROM python:3.12-slim-bookworm

RUN pip install --no-cache-dir "dbt-core>=1.9" "dbt-postgres>=1.9"

WORKDIR /app
COPY dbt/wiki_analytics /app/dbt/wiki_analytics
COPY services/dbt-runner/run.py services/dbt-runner/alerts.py /app/

ENV DBT_PROJECT_DIR=/app/dbt/wiki_analytics
ENV DBT_PROFILES_DIR=/app/dbt/wiki_analytics
ENV PYTHONUNBUFFERED=1

CMD ["python", "/app/run.py"]
