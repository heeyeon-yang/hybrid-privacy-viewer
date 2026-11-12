from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.auth import LoginGuard, LoginRequired, User
from app.config import Settings, get_settings
from app.routers import login, policy, security
from app.storage import LocalStore
from app.templating import templates


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Result Viewer", docs_url=None, redoc_url=None, openapi_url=None)

    app.dependency_overrides[get_settings] = lambda: settings
    app.state.results = LocalStore(settings.data_dir, "results")
    app.state.reports = LocalStore(settings.data_dir, "reports")
    app.state.login_guard = LoginGuard(settings.max_login_failures, settings.lockout_minutes * 60)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="rv_session",
        same_site="strict",
        https_only=False,
    )
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    app.include_router(login.router)
    app.include_router(policy.router)
    app.include_router(security.router)

    @app.get("/healthz")
    def healthz(s: Settings = Depends(get_settings)) -> dict:
        return {"status": "ok", "version": s.git_sha}

    @app.exception_handler(LoginRequired)
    def to_login(request: Request, exc: LoginRequired):
        if request.headers.get("HX-Request"):
            return RedirectResponse("/login?expired=1", status_code=303, headers={"HX-Redirect": "/login?expired=1"})
        return RedirectResponse("/login?expired=1" if request.cookies.get("rv_session") else "/login", status_code=303)

    @app.exception_handler(StarletteHTTPException)
    def http_error(request: Request, exc: StarletteHTTPException):
        data = request.session.get("user") if "session" in request.scope else None
        user = User(**data) if data else None
        return templates.TemplateResponse(
            request, "error.html", {"code": exc.status_code, "user": user}, status_code=exc.status_code
        )

    return app


app = create_app()
