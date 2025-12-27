import os

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.core.db import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as v1_router
from app.core.config import settings


def create_app():
    app = FastAPI(title="Spa API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],  # opcional (útil si luego descargas reportes)
    )

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_ROOT), name="media")

    app.include_router(v1_router)

    # SOLO para dev inicial. En serio: luego usa Alembic.
    # Base.metadata.create_all(engine)
    return app

app = create_app()