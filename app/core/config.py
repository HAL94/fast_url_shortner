# import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# ------------- database ------------
class PostgresSettings(BaseSettings):
    PG_USER: str
    PG_PW: str
    PG_SERVER: str
    PG_PORT: str
    PG_DB: str


class AppSettings(PostgresSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')


settings = AppSettings()
