import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as v1_router
from app.core.audit import register_audit_listeners
from app.core.config import settings
from app.middleware.audit_actor import AuditActorMiddleware


def create_app():
    app = FastAPI(title="Spa API")

    register_audit_listeners()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],  # opcional (útil si luego descargas reportes)
    )

    app.add_middleware(AuditActorMiddleware)



    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_ROOT), name="media")
    # app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(v1_router)

    # SOLO para dev inicial. En serio: luego usa Alembic.
    # Base.metadata.create_all(engine)
    return app

app = create_app()