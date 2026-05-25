from pydantic import BaseModel, Field


class ProfilEleve(BaseModel):
    filiere_souhaitee: str = Field(..., description="Filière souhaitée (ex: informatique)")
    moyenne: float = Field(..., ge=0, le=20, description="Moyenne générale sur 20")
    niveau_vise: str = Field(..., description="Niveau visé : BAC+2, BAC+3 ou BAC+5")


class FormationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nom: str
    filiere: str
    niveau: str
    selectivite: int
    description: str | None


class RecommandationResponse(BaseModel):
    formations: list[FormationOut]
    total: int
