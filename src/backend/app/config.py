from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./app.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = "dev-secret-change-in-production-32b"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24


settings = Settings()
