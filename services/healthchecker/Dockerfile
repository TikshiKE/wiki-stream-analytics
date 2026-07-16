# Build from repository root: docker build -f services/healthchecker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/healthchecker/pyproject.toml services/healthchecker/
COPY services/producer/pyproject.toml services/producer/
COPY services/consumer/pyproject.toml services/consumer/
COPY dashboard/pyproject.toml dashboard/
RUN uv sync --frozen --no-dev --no-editable --no-install-workspace --package healthchecker

COPY services/healthchecker/src services/healthchecker/src
RUN uv sync --frozen --no-dev --no-editable --package healthchecker

FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app

CMD ["python", "-m", "healthchecker"]
