from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import User, require_role
from app.reports import CHECK_LABELS, MACIE_TYPE_LABELS
from app.runs import STEPS, load_run, load_runs
from app.storage import InvalidRunId, LocalStore, check_run_id
from app.templating import templates

router = APIRouter(prefix="/security")


def reports_store(request: Request) -> LocalStore:
    return request.app.state.reports


@router.get("/runs")
def runs(request: Request, user: User = Depends(require_role("security")), store: LocalStore = Depends(reports_store)):
    items = load_runs(store)
    counts = Counter(r.status for r in items)
    return templates.TemplateResponse(
        request, "security/runs.html", {"user": user, "runs": items, "counts": counts, "steps": STEPS}
    )


@router.get("/runs/{run_id}")
def run_detail(
    request: Request, run_id: str, user: User = Depends(require_role("security")), store: LocalStore = Depends(reports_store)
):
    try:
        check_run_id(run_id)
    except InvalidRunId:
        raise HTTPException(404)
    run = load_run(store, run_id)
    if run.review is None and not run.broken:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "security/run_detail.html", {"user": user, "run": run, "steps": STEPS})


@router.get("/failures")
def failures(request: Request, user: User = Depends(require_role("security")), store: LocalStore = Depends(reports_store)):
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
