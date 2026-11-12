"""Write synthetic results/ and reports/ under sample-data/ for local development."""

import csv
import hashlib
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "sample-data"

SIGUNGU = ["서울 강서구", "서울 노원구", "서울 중랑구", "부산 사하구", "대구 달서구", "인천 남동구", "광주 북구", "대전 서구"]
CRISIS = ["단전", "단수", "건강보험료 체납", "통신비 체납", "임대료 체납", "금융 연체"]
MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
HOUSEHOLD = ["1인 가구", "노인 가구", "한부모 가구", "장애인 가구", "일반 가구"]
BENEFIT = {"생계급여": 640_000, "의료급여": 210_000, "주거급여": 320_000, "교육급여": 45_000}
TABLES = {"citizen.csv": 10000, "crisis_signal.csv": 4200, "benefit_payment.csv": 18500}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def scenario1(rng: random.Random, path: Path) -> None:
    base = {"단전": 0.62, "단수": 0.58, "건강보험료 체납": 0.41, "통신비 체납": 0.35, "임대료 체납": 0.47, "금융 연체": 0.29}
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["period", "sigungu", "crisis_type", "households", "linked"])
        for m in MONTHS:
            for g in SIGUNGU:
                for c in CRISIS:
                    n = rng.randint(20, 140)
                    rate = min(0.95, max(0.05, base[c] + rng.uniform(-0.12, 0.12)))
                    w.writerow([m, g, c, n, round(n * rate)])


def scenario2(rng: random.Random, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "household_type", "benefit_type", "recipients", "avg_payment"])
        for i, y in enumerate([2023, 2024, 2025, 2026]):
            for h in HOUSEHOLD:
                for b, pay in BENEFIT.items():
                    n = int(rng.randint(800, 4000) * (1 + 0.04 * i))
                    w.writerow([y, h, b, n, round(pay * (1 + 0.03 * i) * rng.uniform(0.9, 1.1), -2)])


def export_record(run_id: str, at: str, status: str) -> dict:
    files = []
    if status == "exported":
        files = [
            {"key": f"data/run_id={run_id}/{name}", "rows": rows, "sha256": sha(run_id + name)}
            for name, rows in TABLES.items()
        ]
    return {"run_id": run_id, "executed_at": at, "status": status, "files": files}


def review(run_id: str, at: str, k: int = 7, direct_ok: bool = True) -> dict:
    checks = [
        {"item": "direct_identifier", "passed": direct_ok, "value": 0 if direct_ok else 1,
         "reason": None if direct_ok else "crisis_signal.contact_phone 컬럼이 삭제되지 않음"},
        {"item": "generalization", "passed": True, "value": "주소 시군구, 생년 5세 구간", "reason": None},
        {"item": "k_anonymity", "passed": k >= 5, "value": k,
         "reason": None if k >= 5 else f"최소 k={k}, 기준 5 미만 (노원구 90세 이상 1인 가구)"},
    ]
    return {"run_id": run_id, "reviewed_at": at, "passed": all(c["passed"] for c in checks), "checks": checks}


def macie(run_id: str, at: str, hit: str | None = None) -> dict:
    files = []
    for name in TABLES:
        detected = name == hit
        files.append({
            "key": f"data/run_id={run_id}/{name}",
            "detected": detected,
            "types": ["PHONE_NUMBER"] if detected else [],
            "classification": "quarantine" if detected else "clean",
        })
    return {"run_id": run_id, "scanned_at": at, "files": files}


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    rng = random.Random(42)

    runs = [
        ("20261109-01", "2026-11-09T14:00:00+09:00", "ok"),
        ("20261110-01", "2026-11-10T14:00:00+09:00", "macie"),
        ("20261111-01", "2026-11-11T14:00:00+09:00", "k_anon"),
        ("20261111-02", "2026-11-11T16:30:00+09:00", "direct"),
        ("20261112-01", "2026-11-12T14:00:00+09:00", "ok"),
    ]

    for run_id, at, case in runs:
        rep = ROOT / "reports" / f"run_id={run_id}"
        if case == "k_anon":
            write_json(rep / "adequacy_review.json", review(run_id, at, k=2))
            continue
        if case == "direct":
            write_json(rep / "adequacy_review.json", review(run_id, at, direct_ok=False))
            continue

        write_json(rep / "adequacy_review.json", review(run_id, at))
        write_json(rep / "export_record.json", export_record(run_id, at, "exported"))
        later = at.replace("T14:00", "T14:20")
        write_json(rep / "macie_result.json", macie(run_id, later, "crisis_signal.csv" if case == "macie" else None))

        if case == "ok":
            res = ROOT / "results" / f"run_id={run_id}"
            res.mkdir(parents=True, exist_ok=True)
            scenario1(rng, res / "scenario1.csv")
            scenario2(rng, res / "scenario2.csv")
            write_json(res / "manifest.json", {
                "run_id": run_id,
                "generated_at": at.replace("T14:00", "T15:05"),
                "adequacy_passed": True,
                "scenarios": ["scenario1.csv", "scenario2.csv"],
            })


if __name__ == "__main__":
    main()
