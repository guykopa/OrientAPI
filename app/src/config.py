from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://orientapi:orientapi@localhost:5432/orientapi"
    log_level: str = "INFO"
    app_name: str = "OrientAPI"
    app_version: str = "1.0.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
