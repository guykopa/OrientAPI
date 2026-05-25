import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base
from src.models import Formation
from src.schemas import ProfilEleve
from src.services import RecommendationService


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    session.add_all([
        Formation(nom="BTS SIO", filiere="informatique", niveau="BAC+2", selectivite=50),
        Formation(nom="BTS SNIR", filiere="informatique", niveau="BAC+2", selectivite=55),
        Formation(nom="BUT Informatique", filiere="informatique", niveau="BAC+3", selectivite=65),
        Formation(nom="Licence Informatique", filiere="informatique", niveau="BAC+3", selectivite=60),
        Formation(nom="Master IA", filiere="informatique", niveau="BAC+5", selectivite=90),
        Formation(nom="Master MIAGE", filiere="informatique", niveau="BAC+5", selectivite=80),
    ])
    session.commit()

    yield session
    session.close()


def test_recommend_returns_matching_formations(db: Session) -> None:
    service = RecommendationService(db)
    profil = ProfilEleve(filiere_souhaitee="informatique", moyenne=14.0, niveau_vise="BAC+2")
    result = service.recommend(profil)
    assert result.total == 2
    assert all(f.filiere == "informatique" for f in result.formations)
    assert all(f.niveau == "BAC+2" for f in result.formations)


def test_recommend_filters_by_selectivite(db: Session) -> None:
    service = RecommendationService(db)
    # moyenne 10/20 → threshold 50, only selectivite <= 50
    profil = ProfilEleve(filiere_souhaitee="informatique", moyenne=10.0, niveau_vise="BAC+2")
    result = service.recommend(profil)
    assert result.total == 1
    assert result.formations[0].nom == "BTS SIO"


def test_recommend_sorted_by_selectivite_desc(db: Session) -> None:
    service = RecommendationService(db)
    profil = ProfilEleve(filiere_souhaitee="informatique", moyenne=16.0, niveau_vise="BAC+2")
    result = service.recommend(profil)
    selectivites = [f.selectivite for f in result.formations]
    assert selectivites == sorted(selectivites, reverse=True)


def test_recommend_empty_for_unknown_filiere(db: Session) -> None:
    service = RecommendationService(db)
    profil = ProfilEleve(filiere_souhaitee="philosophie", moyenne=18.0, niveau_vise="BAC+3")
    result = service.recommend(profil)
    assert result.total == 0
    assert result.formations == []


def test_recommend_respects_limit(db: Session) -> None:
    service = RecommendationService(db)
    profil = ProfilEleve(filiere_souhaitee="informatique", moyenne=20.0, niveau_vise="BAC+5")
    result = service.recommend(profil, limit=1)
    assert result.total == 1


def test_recommend_zero_moyenne_returns_nothing(db: Session) -> None:
    service = RecommendationService(db)
    # threshold = 0, no formation with selectivite <= 0
    profil = ProfilEleve(filiere_souhaitee="informatique", moyenne=0.0, niveau_vise="BAC+2")
    result = service.recommend(profil)
    assert result.total == 0
