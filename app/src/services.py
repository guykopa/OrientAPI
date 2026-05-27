import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Formation
from src.schemas import FormationOut, ProfilEleve, RecommandationResponse

logger = structlog.get_logger()


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def recommend(self, profil: ProfilEleve, limit: int = 10) -> RecommandationResponse:
        # Translate grade (0-20) to selectivity threshold (0-100)
        threshold = int((profil.moyenne / 20) * 100)

        stmt = (
            select(Formation)
            .where(Formation.filiere == profil.filiere_souhaitee)
            .where(Formation.niveau == profil.niveau_vise)
            .where(Formation.selectivite <= threshold)
            .order_by(Formation.selectivite.desc())
            .limit(limit)
        )

        formations = list(self.db.scalars(stmt))

        logger.info(
            "recommendation_computed",
            filiere=profil.filiere_souhaitee,
            moyenne=profil.moyenne,
            niveau=profil.niveau_vise,
            threshold=threshold,
            results=len(formations),
        )

        return RecommandationResponse(
            formations=[FormationOut.model_validate(f) for f in formations],
            total=len(formations),
        )

    def list_formations(self) -> list[Formation]:
        return list(self.db.scalars(select(Formation).order_by(Formation.filiere, Formation.nom)))

    def get_formation(self, formation_id: int) -> Formation | None:
        return self.db.get(Formation, formation_id)

    def list_filieres(self) -> list[str]:
        rows = self.db.execute(select(Formation.filiere).distinct().order_by(Formation.filiere))
        return [r[0] for r in rows]
