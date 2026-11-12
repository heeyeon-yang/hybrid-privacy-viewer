from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import User, require_role
from app.analyses import list_records
from app.catalog import CATALOG
from app.reports import CHECK_LABELS, MACIE_TYPE_LABELS
from app.runs import STEPS, load_run, load_runs
from app.storage import InvalidId, Store, check_run_id
from app.templating import templates

router = APIRouter(prefix="/security")


def reports_store(request: Request) -> Store:
    return request.app.state.reports


@router.get("/runs")
def runs(request: Request, user: User = Depends(require_role("security")), store: Store = Depends(reports_store)):
    items = load_runs(store)
    counts = Counter(r.status for r in items)
    return templates.TemplateResponse(
        request, "security/runs.html", {"user": user, "runs": items, "counts": counts, "steps": STEPS}
    )


@router.get("/runs/{run_id}")
def run_detail(
    request: Request, run_id: str, user: User = Depends(require_role("security")), store: Store = Depends(reports_store)
):
    try:
        check_run_id(run_id)
    except InvalidId:
        raise HTTPException(404)
    run = load_run(store, run_id)
    if run.review is None and not run.broken:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "security/run_detail.html", {"user": user, "run": run, "steps": STEPS})


@router.get("/failures")
def failures(request: Request, user: User = Depends(require_role("security")), store: Store = Depends(reports_store)):
    items = load_runs(store)
    reasons: Counter = Counter()
    detected: Counter = Counter()
    for run in items:
        if run.review and not run.review.passed:
            for check in run.review.checks:
                if not check.passed:
                    reasons[CHECK_LABELS.get(check.item, check.item)] += 1
        if run.macie:
            for f in run.macie.files:
                for t in f.types:
                    detected[MACIE_TYPE_LABELS.get(t, t)] += 1

    context = {
        "user": user,
        "total": len(items),
        "aborted": sum(1 for r in items if r.status == "중단"),
        "quarantined": sum(1 for r in items if r.status == "격리"),
        "reasons": reasons.most_common(),
        "detected": detected.most_common(),
    }
    return templates.TemplateResponse(request, "security/failures.html", context)


@router.get("/analyses")
def analyses(request: Request, user: User = Depends(require_role("security")), store: Store = Depends(reports_store)):
    records = list_records(store)
    context = {
        "user": user,
        "records": records,
        "catalog": CATALOG,
        "total": len(records),
        "suppressed": sum(r.suppressed_cells or 0 for r in records),
        "with_suppression": sum(1 for r in records if r.suppressed_cells),
        "failed": sum(1 for r in records if r.status == "failed"),
    }
    return templates.TemplateResponse(request, "security/analyses.html", context)
