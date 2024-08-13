from typing import Any, Optional
from pydantic import field_validator
from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DB_URL: str
    DB_TEST_URL: str
    SECRET_KEY_JWT: str
    ALGORITHM: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    REDIS_DOMAIN: str
    REDIS_PORT: int
    REDIS_PASSWORD: Optional[str]
    CLD_NAME: str
    CLD_API_KEY: int
    CLD_API_SECRET: str

    class Config:
        env_file = "python_web_12.V1/.env"
        env_file_encoding = "utf-8"

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any):
        if v not in ["HS256", "HS512"]:
            raise ValueError("algorithm must be HS256 or HS512")
        return v

    # model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")  # noqa


config = Settings()

