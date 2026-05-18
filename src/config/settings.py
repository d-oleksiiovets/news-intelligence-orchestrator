from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from sqlalchemy import URL

class Settings(BaseSettings):
    DB_USER: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="12345", validation_alias="POSTGRES_PASSWORD")
    DB_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST") 
    DB_PORT: int = Field(default=5433, validation_alias="POSTGRES_PORT")
    DB_NAME: str = Field(default="news_production", validation_alias="POSTGRES_DB")

    API_KEY: str | None = None
    LOG_LEVEL: str = "INFO"
    
    @field_validator('API_KEY', mode='before')
    @classmethod
    def validate_api_key(cls, v):
        """Convert empty string or 'none' to None for API_KEY"""
        if not v or (isinstance(v, str) and v.strip().lower() in ('', 'none')):
            return None
        return v if isinstance(v, str) else None

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        extra="ignore"
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2", 
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

settings = Settings()