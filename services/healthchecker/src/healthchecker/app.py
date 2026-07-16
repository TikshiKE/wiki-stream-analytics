"""FastAPI HTTP server exposing aggregated health."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from healthchecker.models import CheckStatus
from healthchecker.runner import CheckRunner


def create_app(runner: CheckRunner) -> FastAPI:
    app = FastAPI(title="Wiki Stream Analytics Healthchecker", version="0.1.0")

    @app.get("/health")
    def health() -> JSONResponse:
        payload = runner.latest.to_dict()
        status_code = 200 if runner.latest.status != CheckStatus.CRITICAL else 503
        return JSONResponse(content=payload, status_code=status_code)

    return app
