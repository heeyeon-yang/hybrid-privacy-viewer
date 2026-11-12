from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import User, require_role
from app.scenarios import SCENARIOS
from app.storage import InvalidRunId, LocalStore
from app.templating import templates

router = APIRouter(prefix="/policy")


def results_store(request: Request) -> LocalStore:
    return request.app.state.results


@router.get("/runs")
def runs(request: Request, user: User = Depends(require_role("policy")), store: LocalStore = Depends(results_store)):
    items = []
    for run_id in store.run_ids():
        manifest = store.read_json(run_id, "manifest.json")
        if manifest:
            items.append(manifest)
    return templates.TemplateResponse(request, "policy/runs.html", {"user": user, "runs": items})


@router.get("/runs/{run_id}/scenarios/{n}")
def scenario(
    request: Request,
    run_id: str,
    n: int,
    user: User = Depends(require_role("policy")),
    store: LocalStore = Depends(results_store),
    region: str = Query(""),
    category: str = Query(""),
    start: str = Query(""),
    end: str = Query(""),
    group: str = Query(""),
    benefit: str = Query(""),
):
    if n not in SCENARIOS:
        raise HTTPException(404)
    spec = SCENARIOS[n]
    try:
        manifest = store.read_json(run_id, "manifest.json")
        df = store.read_csv(run_id, spec.file)
    except InvalidRunId:
        raise HTTPException(404)
    if manifest is None or df is None:
        raise HTTPException(404)

    filters = {"region": region, "category": category, "start": start, "end": end, "group": group, "benefit": benefit}
    view = spec.build(df, filters)
    context = {"user": user, "run": manifest, "n": n, "spec": spec, "scenarios": SCENARIOS, "view": view, "filters": filters}

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, f"policy/_scenario{n}.html", context)
    return templates.TemplateResponse(request, "policy/scenario.html", context)
