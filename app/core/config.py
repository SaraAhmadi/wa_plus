# app/core/config.py
import os
import json  # For the CORS validator
from typing import List, Union, Optional, Any
from pydantic import AnyHttpUrl, field_validator, PostgresDsn, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "Waplus Dashboard"
    PROJECT_VERSION: str = "1.0"
    SSR_DOCUMENT_DATE: str = "May 17, 2025"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Expect List[AnyHttpUrl], default empty list
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Union[List[str], str]:  # Input 'v' can be various things from env
        if isinstance(v, list):
            # If it's already a list (e.g. from default [], or if pydantic-settings already parsed it somehow)
            # Ensure all items are strings for subsequent AnyHttpUrl parsing by Pydantic
            return [str(item) for item in v]
        if isinstance(v, str):
            # If it's a string, try to parse it.
            # Handles comma-separated values: "http://a.com, http://b.com"
            # Also handles if it's a JSON-formatted list string: "[\"http://a.com\", \"http://b.com\"]"
            stripped_v = v.strip()
            if stripped_v.startswith("[") and stripped_v.endswith("]"):
                try:
                    parsed_list = json.loads(stripped_v)
                    if isinstance(parsed_list, list):
                        return [str(item).strip() for item in parsed_list if str(item).strip()]
                    else:  # Parsed to something other than a list
                        raise ValueError(f"BACKEND_CORS_ORIGINS: Expected JSON list, got {type(parsed_list)}")
                except json.JSONDecodeError:
                    # Not a valid JSON list string, fall through to treat as comma-separated
                    # or raise an error if you expect JSON strictly when brackets are present.
                    # For now, let's be lenient and assume it might be a malformed attempt at a list.
                    # If we fall through, and it's not comma-separated valid URLs, Pydantic will catch it later.
                    pass  # Fall through to comma-separated logic

            # Treat as comma-separated string, split, and strip whitespace
            # Filter out empty strings that might result from "url1,,url2" or trailing commas
            return [item.strip() for item in v.split(",") if item.strip()]

        # If v is not a list or string, it's an unexpected type
        raise ValueError(f"BACKEND_CORS_ORIGINS: Invalid input type {type(v)} for value: {v}")

    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "waplus_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "waplus_dashboard_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        data_dict = info.data
        if not data_dict:
            raise ValueError("Cannot assemble DATABASE_URL: dependent field data not available.")
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=str(data_dict.get("POSTGRES_USER")),
            password=str(data_dict.get("POSTGRES_PASSWORD")),
            host=str(data_dict.get("POSTGRES_SERVER")),
            port=str(data_dict.get("POSTGRES_PORT")),
            path=f"/{data_dict.get('POSTGRES_DB') or ''}",
        )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1
    JWT_ALGORITHM: str = "HS256"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        data_dict = info.data
        if not data_dict:
            raise ValueError("Cannot assemble REDIS_URL: dependent field data not available.")
        password_part = f":{data_dict.get('REDIS_PASSWORD')}@" if data_dict.get("REDIS_PASSWORD") else ""
        return f"redis://{password_part}{data_dict.get('REDIS_HOST')}:{data_dict.get('REDIS_PORT')}/{data_dict.get('REDIS_DB')}"

    GEOSERVER_URL: Optional[AnyHttpUrl] = None
    GEOSERVER_ADMIN_USER: Optional[str] = None
    GEOSERVER_ADMIN_PASSWORD: Optional[str] = None
    WA_PLUS_DATA_SOURCE_PATH: str = "/srv/waplus_data/incoming"
    WA_PLUS_PROCESSED_DATA_PATH: str = "/srv/waplus_data/processed"
    MAINTENANCE_MODE: bool = False
    MAX_FILE_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()

if settings.DEBUG:
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Settings loaded: PROJECT_NAME='{settings.PROJECT_NAME}', DEBUG={settings.DEBUG}")
    try:
        sensitive_excluded_settings = settings.model_dump(
            exclude={'POSTGRES_PASSWORD', 'SECRET_KEY', 'REDIS_PASSWORD', 'GEOSERVER_ADMIN_PASSWORD'}
        )
        logger.debug(f"Full settings (excluding sensitive): {sensitive_excluded_settings}")
    except Exception as e:
        logger.error(f"Error dumping settings for debug log: {e}")