from fastapi import Depends, FastAPI

from app.config import Settings, get_settings

app = FastAPI(title="Coconut Result App", docs_url=None, redoc_url=None)


@app.get("/healthz")
def healthz(settings: Settings = Depends(get_settings)) -> dict:
    """k3s liveness/readiness probe 용. 외부 의존(S3 등)은 확인하지 않음."""
    return {"status": "ok", "version": settings.git_sha}
