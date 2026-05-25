from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Formation(Base):
    __tablename__ = "formations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    filiere: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    niveau: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    selectivite: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
