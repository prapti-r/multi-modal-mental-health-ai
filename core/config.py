from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator, EmailStr
from typing import List, Any
from pydantic import EmailStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    #  App
    APP_NAME: str = "Eunoia"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str # Must be set in .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 10

    # Database (PostgreSQL) 
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "eunoia"

    # Mail Settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis 
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # CORS 
    ALLOWED_ORIGINS: List[str] | str = ["http://localhost:8081"]  # Expo dev default

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return [str(v)]

    # Media / Upload constraints
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_MIME_TYPES: List[str] = ["video/mp4", "audio/wav", "audio/mpeg"]
    MEDIA_RETENTION_MINUTES: int = 10 # Raw media must be purged after this

    # AI / ML 
    BERT_MODEL_NAME: str = "distilroberta-base"
    WHISPER_MODEL_SIZE: str = "base" # base | small | medium
    FUSION_MODEL_VERSION: str = "v1.0.0"

    # Performance targets 
    TEXT_RESPONSE_TIMEOUT_SECONDS: int = 3
    TARGET_EMOTION_ACCURACY: float = 0.70

    # Risk thresholds 
    RISK_MODERATE_THRESHOLD: int = 31
    RISK_SEVERE_THRESHOLD: int = 60

settings = Settings() # type: ignore[call-arg]