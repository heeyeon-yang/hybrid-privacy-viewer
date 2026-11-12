from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.reports import CHECK_LABELS, MACIE_TYPE_LABELS

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def fmt_dt(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


def fmt_num(value) -> str:
    try:
        return f"{value:,.0f}"
    except (TypeError, ValueError):
        return str(value)


templates.env.filters["dt"] = fmt_dt
templates.env.filters["num"] = fmt_num
templates.env.globals["CHECK_LABELS"] = CHECK_LABELS
templates.env.globals["MACIE_TYPE_LABELS"] = MACIE_TYPE_LABELS
templates.env.globals["session_minutes"] = lambda: get_settings().session_idle_minutes
