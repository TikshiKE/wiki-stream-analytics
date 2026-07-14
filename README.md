# Wiki Stream Analytics

Real-time analytics pipeline for Wikipedia edits: **Wikimedia EventStreams → Kafka →
PostgreSQL → dbt → Streamlit dashboard**, orchestrated by Airflow, monitored by a custom
healthchecker with Telegram alerts. Built as a production-style portfolio project:
containerized, tested, deployed to Railway via GitHub Actions.

> Work in progress — see [PLAN.md](PLAN.md) for the roadmap and architecture.

## Local development

```bash
docker compose up -d   # Kafka, Postgres, Redis, Kafka UI (localhost:8088)
```
