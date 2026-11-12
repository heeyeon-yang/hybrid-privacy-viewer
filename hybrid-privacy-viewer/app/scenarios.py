from dataclasses import dataclass
from typing import Callable

import pandas as pd


def _options(series: pd.Series) -> list[str]:
    return sorted(str(v) for v in series.dropna().unique())


def scenario1(df: pd.DataFrame, f: dict) -> dict:
    options = {
        "region": _options(df["sigungu"]),
        "category": _options(df["crisis_type"]),
        "period": _options(df["period"]),
    }
    if f["region"]:
        df = df[df["sigungu"] == f["region"]]
    if f["category"]:
        df = df[df["crisis_type"] == f["category"]]
    if f["start"]:
        df = df[df["period"] >= f["start"]]
    if f["end"]:
        df = df[df["period"] <= f["end"]]

    total = int(df["households"].sum())
    linked = int(df["linked"].sum())

    by_type = df.groupby("crisis_type")[["households", "linked"]].sum()
    by_type["rate"] = (by_type["linked"] / by_type["households"] * 100).round(1)
    by_type = by_type.sort_values("rate")

    by_region = df.groupby("sigungu")[["households", "linked"]].sum()
    by_region["unlinked"] = by_region["households"] - by_region["linked"]
    by_region["unlinked_rate"] = (by_region["unlinked"] / by_region["households"] * 100).round(1)
    by_region = by_region.sort_values("unlinked_rate", ascending=False)

    return {
        "options": options,
        "summary": {
            "households": total,
            "linked": linked,
            "rate": round(linked / total * 100, 1) if total else 0,
        },
        "by_type": by_type.reset_index().to_dict("records"),
        "by_region": by_region.reset_index().to_dict("records"),
        "chart": {
            "labels": list(by_type.index),
            "data": by_type["rate"].tolist(),
        },
    }


def scenario2(df: pd.DataFrame, f: dict) -> dict:
    options = {
        "year": _options(df["year"]),
        "group": _options(df["household_type"]),
        "benefit": _options(df["benefit_type"]),
    }
    if f["start"]:
        df = df[df["year"] >= int(f["start"])]
    if f["end"]:
        df = df[df["year"] <= int(f["end"])]
    if f["group"]:
        df = df[df["household_type"] == f["group"]]
    if f["benefit"]:
        df = df[df["benefit_type"] == f["benefit"]]

    df = df.assign(total=df["recipients"] * df["avg_payment"])

    by_year = df.groupby(["year", "benefit_type"])[["recipients", "total"]].sum().reset_index()
    years = sorted(by_year["year"].unique().tolist())
    series = []
    for benefit, rows in by_year.groupby("benefit_type"):
        counts = dict(zip(rows["year"], rows["recipients"]))
        series.append({"name": benefit, "data": [int(counts.get(y, 0)) for y in years]})

    table = df.groupby(["year", "household_type", "benefit_type"])[["recipients", "total"]].sum()
    table["avg_payment"] = (table["total"] / table["recipients"]).round(0)
    table = table.reset_index().sort_values(["year", "household_type", "benefit_type"], ascending=[False, True, True])

    return {
        "options": options,
        "summary": {
            "recipients": int(df[df["year"] == df["year"].max()]["recipients"].sum()) if len(df) else 0,
            "latest_year": int(df["year"].max()) if len(df) else None,
        },
        "rows": table.to_dict("records"),
        "chart": {"years": [str(y) for y in years], "series": series},
    }


@dataclass
class Scenario:
    title: str
    file: str
    build: Callable[[pd.DataFrame, dict], dict]


SCENARIOS = {
    1: Scenario("위기가구 지원 연계율", "scenario1.csv", scenario1),
    2: Scenario("기초생활보장 수급 현황", "scenario2.csv", scenario2),
}
