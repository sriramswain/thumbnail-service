import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.errors import register_exception_handlers

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").strip().split(",")


def create_app() -> FastAPI:
    app = FastAPI(title="Thumbnail Service", version="0.1.0")

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

