# Railway deployment guide

Step-by-step setup for production on Railway. **Complete each step and confirm before moving to the next.**

Prerequisites: GitHub repo `TikshiKE/wiki-stream-analytics`, `main` branch up to date, Railway account with billing enabled.

Everything runs on Railway — **no GitHub Pages**.

---

## How dbt docs work on Railway

dbt docs are **static HTML** (~2–5 MB). On each push to `main`, GitHub Actions:

1. Spins up Postgres in CI, applies migrations + seed fixtures
2. Runs `dbt docs generate`
3. Bakes the HTML into a tiny **nginx** image → pushes to GHCR
4. `railway redeploy --service dbt-docs` pulls the new image

The `dbt-docs` service needs **no Postgres/Redis** at runtime — only nginx serving files.

---

## Phase 0 — GitHub configuration (one-time)

### Step 0.1 — GitHub Secret

| Secret | Where to get it |
|--------|-----------------|
| `RAILWAY_TOKEN` | Railway → **Project** → Settings → **Tokens** → Generate **Project Token** (not account token) |

`GITHUB_TOKEN` is provided automatically for GHCR push.

### Step 0.2 — GHCR package visibility

After first `build-deploy.yml` run:

1. GitHub → **Packages** → open each `wiki-stream-analytics-*` image (6 packages)
2. **Package settings** → **Change visibility** → **Public** (Railway pulls without registry credentials)

**Stop here and confirm:** `RAILWAY_TOKEN` secret added (can add after creating Railway project).

---

## Phase 1 — Railway project skeleton

### Step 1.1 — Create project

1. [railway.app](https://railway.app) → **New Project** → **Empty Project**
2. Name: `wiki-stream-analytics`

### Step 1.2 — Add Postgres

1. **+ New** → **Database** → **PostgreSQL**
2. Rename service to `postgres`
3. Note variables: `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### Step 1.3 — Add Redis

1. **+ New** → **Database** → **Redis**
2. Rename to `redis`
3. Note `REDIS_URL` (or construct from provided host/port/password)

**Stop here and confirm:** Postgres + Redis are running.

---

## Phase 2 — Kafka (Docker, single broker)

### Step 2.1 — Create Kafka service

1. **+ New** → **Empty Service** → **Docker Image**
2. Image: `apache/kafka:4.0.0`
3. Rename service to `kafka`

### Step 2.2 — Kafka environment variables

Set on the `kafka` service (private networking — **no public port**):

```env
KAFKA_NODE_ID=1
KAFKA_PROCESS_ROLES=broker,controller
KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
KAFKA_LISTENERS=INTERNAL://:9092,CONTROLLER://:9093
KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka:9092
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT
KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL
KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
KAFKA_AUTO_CREATE_TOPICS_ENABLE=false
KAFKA_LOG_RETENTION_HOURS=24
```

### Step 2.3 — Kafka volume

1. Kafka service → **Settings** → **Volumes** → Add volume mount: `/var/lib/kafka/data`
2. Set RAM limit: **1024 MB**

**Stop here and confirm:** Kafka service is healthy (check deploy logs).

---

## Phase 3 — Shared environment variables

Create **Shared Variables** at project level (or duplicate per service):

```env
POSTGRES_USER=${{postgres.PGUSER}}
POSTGRES_PASSWORD=${{postgres.PGPASSWORD}}
POSTGRES_DB=${{postgres.PGDATABASE}}
KAFKA_TOPIC_EVENTS=wiki.recentchange
KAFKA_TOPIC_DLQ=wiki.recentchange.dlq
KAFKA_CONSUMER_GROUP=pg-writer
SSE_URL=https://stream.wikimedia.org/v2/stream/recentchange
SSE_USER_AGENT=wiki-stream-analytics/0.1 (https://github.com/TikshiKE/wiki-stream-analytics; your@email.com)
RETENTION_DAYS=14
DBT_TARGET=prod
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Replace `SSE_USER_AGENT` email with your contact.

**Stop here and confirm:** shared variables created.

---

## Phase 4 — Application services (GHCR images)

For each service below: **+ New** → **Empty Service** → **Deploy from Docker Image**:

| Service name | Image | Public URL | RAM |
|--------------|-------|------------|-----|
| `producer` | `ghcr.io/tikshike/wiki-stream-analytics-producer:latest` | No | 256 MB |
| `consumer` | `ghcr.io/tikshike/wiki-stream-analytics-consumer:latest` | No | 512 MB |
| `dashboard` | `ghcr.io/tikshike/wiki-stream-analytics-dashboard:latest` | **Yes** | 512 MB |
| `healthchecker` | `ghcr.io/tikshike/wiki-stream-analytics-healthchecker:latest` | Optional | 256 MB |
| `airflow` | `ghcr.io/tikshike/wiki-stream-analytics-airflow:latest` | Optional (8080) | 1536 MB |
| `dbt-docs` | `ghcr.io/tikshike/wiki-stream-analytics-dbt-docs:latest` | **Yes** | 128 MB |

> Use lowercase `tikshike` in GHCR paths. Pin to `:latest` for auto-pull on redeploy.

### Step 4.1 — producer

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Step 4.2 — consumer

Runs migrations on start (entrypoint). Set **one** of:

**Option A (recommended on Railway):**

```env
DATABASE_URL=${{postgres.DATABASE_URL}}
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
REDIS_URL=${{redis.REDIS_URL}}
```

**Option B (manual copy from postgres → Variables → reveal values):**

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
POSTGRES_HOST=${{postgres.PGHOST}}
POSTGRES_PORT=${{postgres.PGPORT}}
POSTGRES_USER=${{postgres.PGUSER}}
POSTGRES_PASSWORD=${{postgres.PGPASSWORD}}
POSTGRES_DB=${{postgres.PGDATABASE}}
REDIS_URL=${{redis.REDIS_URL}}
```

> Do not type `postgres` / `wiki` by hand — copy exact `PGUSER` / `PGPASSWORD` from the postgres service.

### Step 4.3 — dashboard

```env
POSTGRES_HOST=${{postgres.PGHOST}}
POSTGRES_PORT=${{postgres.PGPORT}}
POSTGRES_DB=${{postgres.PGDATABASE}}
POSTGRES_RO_USER=wiki_ro
POSTGRES_RO_PASSWORD=wiki_ro
REDIS_URL=${{redis.REDIS_URL}}
GITHUB_REPO_URL=https://github.com/TikshiKE/wiki-stream-analytics
```

> **Important:** `POSTGRES_DB` must match Railway (`railway`), not the local default `wiki`.

**Healthcheck:** path `/_stcore/health`, port `8501`

Generate public domain in Railway → **Settings** → **Networking** → **Generate domain**

### Step 4.4 — healthchecker

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
POSTGRES_HOST=${{postgres.PGHOST}}
POSTGRES_PORT=${{postgres.PGPORT}}
POSTGRES_USER=${{postgres.PGUSER}}
POSTGRES_PASSWORD=${{postgres.PGPASSWORD}}
POSTGRES_DB=${{postgres.PGDATABASE}}
REDIS_URL=${{redis.REDIS_URL}}
DASHBOARD_URL=https://<your-dashboard-domain>.up.railway.app
HEALTH_PORT=8090
```

Use Railway private DNS for `dashboard` if available, or public dashboard URL.

**Healthcheck:** path `/health`, port `8090`

### Step 4.5 — airflow

Generate Fernet key locally: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

```env
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://${{postgres.PGUSER}}:${{postgres.PGPASSWORD}}@${{postgres.PGHOST}}:${{postgres.PGPORT}}/airflow_meta
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false
AIRFLOW__CORE__DEFAULT_TIMEZONE=utc
AIRFLOW__CORE__FERNET_KEY=<your-fernet-key>
_AIRFLOW_DB_MIGRATE=true
_AIRFLOW_WWW_USER_CREATE=true
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=<choose-strong-password>
POSTGRES_HOST=${{postgres.PGHOST}}
POSTGRES_PORT=${{postgres.PGPORT}}
POSTGRES_USER=${{postgres.PGUSER}}
POSTGRES_PASSWORD=${{postgres.PGPASSWORD}}
POSTGRES_DB=${{postgres.PGDATABASE}}
DBT_TARGET=prod
```

`airflow_meta` database is created by consumer migrations on first deploy.

**Start command:** `standalone` (Settings → Deploy → Custom Start Command). Without it you get `airflow command error: GROUP_OR_COMMAND required`.

**Public networking:** target port **8080**.

### Step 4.6 — dbt-docs

No environment variables needed — static nginx on port **8080**.

1. Create service from `ghcr.io/tikshike/wiki-stream-analytics-dbt-docs:latest`
2. Set RAM limit: **128 MB**
3. **Networking** → **Generate domain** (public)
4. In service settings, set **port** to `8080` if Railway does not auto-detect

Enable **Configure Auto Updates** → **Latest tag** so new docs deploy after CI (optional backup to `railway redeploy` in Actions).

**Stop here and confirm:** all 6 GHCR services created with correct settings.

---

## Phase 5 — First deploy

### Step 5.1 — Push to main

Push to `main` → GitHub Actions runs `ci.yml` and `build-deploy.yml`.

### Step 5.2 — Verify GHCR

GitHub → **Packages** — 6 images with `latest` tag (including `wiki-stream-analytics-dbt-docs`).

### Step 5.3 — Trigger Railway redeploy

Either wait for `build-deploy.yml` (`railway redeploy`) or manually redeploy each service in Railway UI.

### Step 5.4 — Watch consumer logs

Consumer must run `sql/migrate.py` successfully (creates `raw`, `airflow_meta`, `wiki_ro` grants).

**Stop here and confirm:** consumer logs show migrations applied, events flowing.

---

## Phase 6 — Smoke test

| Check | How |
|-------|-----|
| Dashboard live | Open public dashboard URL — live counter > 0 |
| Health | `curl https://<healthchecker-domain>/health` → `"status":"ok"` |
| Airflow | Open Airflow URL → DAGs `dbt_hourly`, `maintenance_daily` green |
| dbt docs | Open public `dbt-docs` URL → lineage graph, model descriptions |
| CI | GitHub Actions all green on `main` |

### Manual failure test

1. Stop `consumer` in Railway
2. Within ~5 min: healthchecker `/health` → 503, Telegram log/alert (if configured)
3. Start `consumer` → recovery alert, `/health` → 200

---

## Deploy method: Railway CLI (chosen)

**Why CLI over webhooks:** one `RAILWAY_TOKEN` secret redeploys all 6 GHCR services in a single workflow step; no per-service webhook URLs to manage. Images use `:latest`; `railway redeploy` pulls the new digest after GHCR push.

**Alternative:** Railway deploy hooks (one HTTP POST URL per service) — simpler per-service but 6 secrets and no atomic multi-service rollout.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Railway can't pull image | Make GHCR package **public** |
| Consumer migration fails | Check Postgres credentials; redeploy consumer |
| Kafka connection refused | Verify `KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka:9092` |
| Dashboard empty marts | Wait for Airflow `dbt_hourly` or trigger manually |
| dbt-docs 404 / blank | Redeploy after first CI build; check port 8080 |
| `railway redeploy` fails in CI | Service names must match Railway exactly (`producer`, `dbt-docs`, etc.) |
