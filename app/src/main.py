from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from src.auth import create_access_token, require_token, verify_credentials
from src.config import settings
from src.database import Base, engine, get_db
from src.models import Formation  # noqa: F401 — ensures model is registered before create_all
from src.schemas import FormationOut, ProfilEleve, RecommandationResponse, Token
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


@app.post("/token", response_model=Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    if not verify_credentials(form_data.username, form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(form_data.username))


@app.get("/formations", response_model=list[FormationOut])
def list_formations(
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> list[FormationOut]:
    return RecommendationService(db).list_formations()


@app.get("/formations/{formation_id}", response_model=FormationOut)
def get_formation(
    formation_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> FormationOut:
    formation = RecommendationService(db).get_formation(formation_id)
    if not formation:
        raise HTTPException(status_code=404, detail="Formation non trouvée")
    return formation


@app.get("/filieres", response_model=list[str])
def list_filieres(
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> list[str]:
    return RecommendationService(db).list_filieres()


@app.post("/recommend", response_model=RecommandationResponse)
def recommend(
    profil: ProfilEleve,
    db: Session = Depends(get_db),
    _: str = Depends(require_token),
) -> RecommandationResponse:
    return RecommendationService(db).recommend(profil)
