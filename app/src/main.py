from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from src.config import settings
from src.database import Base, engine, get_db
from src.models import Formation  # noqa: F401 — ensures model is registered before create_all
from src.schemas import ProfilEleve, RecommandationResponse
from src.seed import seed
from src.services import RecommendationService

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    from src.database import SessionLocal

    with SessionLocal() as db:
        seed(db)
    logger.info("startup_complete", app=settings.app_name, version=settings.app_version)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommandationResponse)
def recommend(
    profil: ProfilEleve,
    db: Session = Depends(get_db),
) -> RecommandationResponse:
    return RecommendationService(db).recommend(profil)
