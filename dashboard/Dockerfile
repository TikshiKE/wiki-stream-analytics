# Build from repository root: docker build -f dashboard/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY dashboard/pyproject.toml dashboard/
COPY services/producer/pyproject.toml services/producer/
COPY services/consumer/pyproject.toml services/consumer/
COPY services/healthchecker/pyproject.toml services/healthchecker/
RUN uv sync --frozen --no-dev --no-editable --no-install-workspace --package dashboard

COPY dashboard/src dashboard/src
RUN uv sync --frozen --no-dev --no-editable --package dashboard

FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dashboard/src /app/dashboard/src
COPY dashboard/.streamlit /app/dashboard/.streamlit
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/dashboard/src"
USER app
WORKDIR /app/dashboard
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
