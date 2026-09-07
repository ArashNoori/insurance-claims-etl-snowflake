"""
Unit tests for src/transform.py

These test the pure transformation functions (clean_claims, enrich_claims,
build_region_summary) using small in-memory DataFrames — no real files or
network calls are needed, which is exactly why these functions were written
as pure functions in the first place.
"""

import pandas as pd
import pytest

from src.transform import build_region_summary, clean_claims, enrich_claims


# ---------- clean_claims ----------

def test_clean_claims_removes_duplicate_rows():
    df = pd.DataFrame({
        "age": [30, 30],
        "bmi": [25.0, 25.0],
        "charges": [1000.0, 1000.0],
        "region": ["southeast", "southeast"],
        "smoker": ["no", "no"],
    })
    result = clean_claims(df)
    assert len(result) == 1


def test_clean_claims_drops_rows_with_missing_required_fields():
    df = pd.DataFrame({
        "age": [30, None],
        "bmi": [25.0, 27.0],
        "charges": [1000.0, 2000.0],
        "region": ["southeast", "northwest"],
        "smoker": ["no", "yes"],
    })
    result = clean_claims(df)
    assert len(result) == 1
    assert result.iloc[0]["age"] == 30


def test_clean_claims_drops_invalid_age_and_charges():
    df = pd.DataFrame({
        "age": [30, -5, 40],
        "bmi": [25.0, 27.0, 22.0],
        "charges": [1000.0, 2000.0, -50.0],
        "region": ["southeast", "northwest", "southwest"],
        "smoker": ["no", "yes", "no"],
    })
    result = clean_claims(df)
    # only the first row (age=30, charges=1000) is fully valid
    assert len(result) == 1
    assert result.iloc[0]["age"] == 30


def test_clean_claims_keeps_valid_rows_untouched():
    df = pd.DataFrame({
        "age": [30, 45],
        "bmi": [25.0, 31.0],
        "charges": [1000.0, 5000.0],
        "region": ["southeast", "northwest"],
        "smoker": ["no", "yes"],
    })
    result = clean_claims(df)
    assert len(result) == 2


# ---------- enrich_claims ----------

def test_enrich_claims_adds_eur_conversion():
    df = pd.DataFrame({
        "age": [30],
        "bmi": [25.0],
        "charges": [1000.0],
        "region": ["southeast"],
        "smoker": ["no"],
    })
    result = enrich_claims(df, usd_to_eur=0.9)
    assert result.iloc[0]["charges_eur"] == 900.0


@pytest.mark.parametrize(
    "smoker,bmi,expected",
    [
        ("yes", 31.0, "high"),     # smoker + high bmi
        ("yes", 22.0, "medium"),   # smoker but healthy bmi
        ("no", 32.0, "medium"),    # non-smoker but high bmi
        ("no", 22.0, "low"),       # non-smoker, healthy bmi
    ],
)
def test_enrich_claims_risk_segment_logic(smoker, bmi, expected):
    df = pd.DataFrame({
        "age": [30],
        "bmi": [bmi],
        "charges": [1000.0],
        "region": ["southeast"],
        "smoker": [smoker],
    })
    result = enrich_claims(df, usd_to_eur=1.0)
    assert result.iloc[0]["risk_segment"] == expected


def test_enrich_claims_does_not_mutate_input():
    df = pd.DataFrame({
        "age": [30],
        "bmi": [25.0],
        "charges": [1000.0],
        "region": ["southeast"],
        "smoker": ["no"],
    })
    enrich_claims(df, usd_to_eur=0.9)
    assert "charges_eur" not in df.columns


# ---------- build_region_summary ----------

def test_build_region_summary_groups_and_counts_correctly():
    df = pd.DataFrame({
        "region": ["southeast", "southeast", "northwest"],
        "smoker": ["yes", "yes", "no"],
        "charges": [1000.0, 3000.0, 500.0],
        "charges_eur": [900.0, 2700.0, 450.0],
    })
    summary = build_region_summary(df)

    se_smokers = summary[(summary["region"] == "southeast") & (summary["smoker"] == "yes")]
    assert se_smokers.iloc[0]["claim_count"] == 2
    assert se_smokers.iloc[0]["avg_charges_usd"] == 2000.0
    assert se_smokers.iloc[0]["avg_charges_eur"] == 1800.0

    nw_nonsmokers = summary[(summary["region"] == "northwest") & (summary["smoker"] == "no")]
    assert nw_nonsmokers.iloc[0]["claim_count"] == 1


def test_build_region_summary_is_sorted_by_region_and_smoker():
    df = pd.DataFrame({
        "region": ["southwest", "northeast", "southwest"],
        "smoker": ["yes", "no", "no"],
        "charges": [1000.0, 2000.0, 1500.0],
        "charges_eur": [900.0, 1800.0, 1350.0],
    })
    summary = build_region_summary(df)
    regions = summary["region"].tolist()
    assert regions == sorted(regions)
