import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60

    # Business
    TIMEZONE: str = "America/Santo_Domingo"
    CURRENCY: str = "DOP"
    BUSINESS_OPEN_TIME: str = "09:00"   # HH:MM
    BUSINESS_CLOSE_TIME: str = "18:00"  # HH:MM

    # CORS_ORIGINS: str = "http://localhost:4200"
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    FRONTEND_URL: str = "http://localhost:4200"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_NAME: str = "Spa App"
    SMTP_FROM_EMAIL: str

    RESET_TOKEN_TTL_MINUTES: int = 30

    WHATSAPP_PROVIDER: str = "meta"
    WA_PHONE_NUMBER_ID: str | None = None
    WA_ACCESS_TOKEN: str | None = None
    WA_BUSINESS_ACCOUNT_ID: str | None = None
    WA_DEFAULT_LANG: str = "es"

    MEDIA_ROOT: str = "media"
    MEDIA_URL_PREFIX: str = "/media"  # ruta pública

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config  = SettingsConfigDict(
        env_file = ".env",
        extra = "forbid",
    )


settings = Settings()