# Running dbt

In normal operation **dbt runs automatically** via the Airflow `dbt_hourly` DAG
(`docker compose up -d` locally, Airflow service on Railway) — no manual steps required.

## Automatic runs (default)

Airflow triggers `dbt build` every hour (`@hourly`, `catchup=False`).
Set `DBT_TARGET=prod` on Railway; use `dev` locally.

## Manual run (debug only)

Prerequisites: Docker stack running so `raw.recentchange` has data.

```powershell
cd dbt/wiki_analytics
$env:DBT_PROFILES_DIR = (Get-Location)
uv run --project ../.. dbt deps
uv run --project ../.. dbt build --profiles-dir .
uv run --project ../.. dbt docs generate --profiles-dir .
uv run --project ../.. dbt docs serve --profiles-dir .
```

Environment variables (defaults match `.env.example`):

| Variable | Default |
|----------|---------|
| `POSTGRES_HOST` | localhost |
| `POSTGRES_PORT` | 5433 |
| `POSTGRES_USER` | wiki |
| `POSTGRES_PASSWORD` | wiki |
| `POSTGRES_DB` | wiki |
| `DBT_TARGET` | dev |

Schemas created: `staging` (views), `marts` (tables / incremental).
