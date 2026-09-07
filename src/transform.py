"""
transform.py — Clean, enrich, and reshape the raw insurance claims data.

Reads the raw outputs from data/raw/ (produced by extract.py), joins the
claims data with the USD->EUR exchange rate, derives business metrics,
and writes analysis-ready tables to data/processed/ (the "silver/gold" layer).
"""

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_latest_exchange_rate() -> float:
    """Load the most recently saved exchange rate snapshot."""
    rate_files = sorted(RAW_DIR.glob("exchange_rate_*.json"))
    if not rate_files:
        raise FileNotFoundError("No exchange rate snapshot found in data/raw/. Run extract.py first.")
    latest_file = rate_files[-1]
    payload = json.loads(latest_file.read_text().replace("'", '"'))
    rate = payload["rates"]["EUR"]
    logger.info("Loaded exchange rate USD->EUR = %.4f from %s", rate, latest_file.name)
    return rate


def clean_claims(df: pd.DataFrame) -> pd.DataFrame:
    """Basic data quality checks and cleaning."""
    before = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=["age", "bmi", "charges", "region"])
    df = df[(df["age"] > 0) & (df["charges"] > 0)]
    after = len(df)
    logger.info("Cleaned claims data: %d -> %d rows (%d removed)", before, after, before - after)
    return df


def enrich_claims(df: pd.DataFrame, usd_to_eur: float) -> pd.DataFrame:
    """Add derived columns: EUR-normalized charges and a simple risk segment."""
    df = df.copy()
    df["charges_eur"] = (df["charges"] * usd_to_eur).round(2)

    def risk_segment(row):
        if row["smoker"] == "yes" and row["bmi"] >= 30:
            return "high"
        if row["smoker"] == "yes" or row["bmi"] >= 30:
            return "medium"
        return "low"

    df["risk_segment"] = df.apply(risk_segment, axis=1)
    return df


def build_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate: average claim cost and count, by region and smoker status."""
    summary = (
        df.groupby(["region", "smoker"])
        .agg(
            claim_count=("charges", "count"),
            avg_charges_usd=("charges", "mean"),
            avg_charges_eur=("charges_eur", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values(["region", "smoker"])
    )
    return summary


def main():
    claims_raw = pd.read_csv(RAW_DIR / "insurance_claims_raw.csv")
    usd_to_eur = load_latest_exchange_rate()

    claims_clean = clean_claims(claims_raw)
    claims_enriched = enrich_claims(claims_clean, usd_to_eur)
    region_summary = build_region_summary(claims_enriched)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    claims_out = PROCESSED_DIR / "claims_enriched.csv"
    summary_out = PROCESSED_DIR / "region_summary.csv"
    claims_enriched.to_csv(claims_out, index=False)
    region_summary.to_csv(summary_out, index=False)

    logger.info("Saved %d enriched claim rows to %s", len(claims_enriched), claims_out)
    logger.info("Saved %d summary rows to %s", len(region_summary), summary_out)
    logger.info("Transform complete.")


if __name__ == "__main__":
    main()