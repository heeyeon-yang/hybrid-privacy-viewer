from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RESULT_APP_", env_file=".env", extra="ignore")

    app_name: str = "result-app"
    # 빌드 시 커밋 SHA 7자리가 주입됨 (Dockerfile ARG GIT_SHA)
    git_sha: str = "dev"

    # S3 정제 버킷 (읽기 전용, results/ reports/ 만 사용)
    s3_bucket: str = ""
    s3_region: str = "ap-northeast-2"
    results_prefix: str = "results/"
    reports_prefix: str = "reports/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
