from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RESULT_APP_", env_file=".env", extra="ignore")

    git_sha: str = "dev"
    session_secret: str = "change-me"
    session_idle_minutes: int = 30

    max_login_failures: int = 5
    lockout_minutes: int = 15

    # local: read from data_dir with the same key layout as the S3 bucket
    data_source: str = "local"
    data_dir: Path = Path("sample-data")
    accounts_file: Path = Path("accounts.dev.json")

    s3_bucket: str = ""
    s3_region: str = "ap-northeast-2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
