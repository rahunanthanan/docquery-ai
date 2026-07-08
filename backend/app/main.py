"""DocQuery AI — FastAPI application entrypoint.

Task 1 scope: application factory + health endpoint only.
Feature routers (auth, documents, qa, review, audit) are added in later tasks.
"""

from fastapi import FastAPI

from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
        }

    return app


app = create_app()
