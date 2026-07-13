from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "MSCI Indonesia Stock Recommendation API"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"

    data_dir: Path = BACKEND_DIR / "data"

    # Digunakan untuk development lokal.
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

        return origins or ["*"]


settings = Settings()