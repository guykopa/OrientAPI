from pathlib import Path

from pydantic_settings import BaseSettings

_here = Path(__file__).parent  # src/
_env_file = _here.parent / ".env"  # app/.env


class Settings(BaseSettings):
    database_url: str = "postgresql://orientapi:orientapi@localhost:5432/orientapi"
    log_level: str = "INFO"
    app_name: str = "OrientAPI"
    app_version: str = "1.0.0"

    jwt_secret: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    api_username: str = "demo"
    api_password: str = "orientops2026"

    model_config = {"env_file": str(_env_file), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
