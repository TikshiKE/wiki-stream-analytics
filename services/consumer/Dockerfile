FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/consumer/pyproject.toml services/consumer/
COPY services/producer/pyproject.toml services/producer/
COPY services/healthchecker/pyproject.toml services/healthchecker/
RUN uv sync --frozen --no-dev --no-editable --no-install-workspace --package consumer

COPY services/consumer/src services/consumer/src
COPY sql sql
RUN uv sync --frozen --no-dev --no-editable --package consumer

FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/sql /app/sql
ENV PATH="/app/.venv/bin:$PATH"
USER app

ENTRYPOINT ["sh", "-c", "python /app/sql/migrate.py && exec python -m consumer"]
