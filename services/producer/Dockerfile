# Build from the repository root: docker build -f services/producer/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Workspace metadata first: dependency layer is cached until pyprojects change
COPY pyproject.toml uv.lock ./
COPY services/producer/pyproject.toml services/producer/
COPY services/consumer/pyproject.toml services/consumer/
COPY services/healthchecker/pyproject.toml services/healthchecker/
RUN uv sync --frozen --no-dev --no-editable --no-install-workspace --package producer

COPY services/producer/src services/producer/src
RUN uv sync --frozen --no-dev --no-editable --package producer

FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
USER app

CMD ["python", "-m", "producer"]
