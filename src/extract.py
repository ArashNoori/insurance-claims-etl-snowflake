"""
extract.py — Extract raw data for the insurance claims ETL pipeline.

Sources:
1. Insurance claims CSV (US Medical Insurance Costs dataset) — file-based extract
2. Live USD->EUR exchange rate from the Frankfurter API — API-based extract

Both raw outputs are saved unmodified to data/raw/ (the "bronze" layer),
so the pipeline is reproducible without re-hitting the network every run.
"""
import io
import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
CSV_SOURCE_URL = "https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/insurance.csv"
FX_API_URL = "https://api.frankfurter.dev/v1/latest"


def extract_claims_csv() -> pd.DataFrame:
    """Download the insurance claims CSV and save it unmodified to data/raw/."""
    logger.info("Extracting insurance claims data from %s", CSV_SOURCE_URL)
    response = requests.get(CSV_SOURCE_URL, timeout=10)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "insurance_claims_raw.csv"
    df.to_csv(out_path, index=False)
    logger.info("Saved %d rows to %s", len(df), out_path)
    return df


def extract_exchange_rate(base: str = "USD", target: str = "EUR") -> float:
    """Fetch today's USD->EUR exchange rate from the Frankfurter API."""
    logger.info("Extracting %s->%s exchange rate from Frankfurter API", base, target)
    params = {"base": base, "symbols": target}
    response = requests.get(FX_API_URL, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    rate = payload["rates"][target]
    logger.info("Exchange rate %s->%s = %.4f (as of %s)", base, target, rate, payload["date"])

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"exchange_rate_{date.today().isoformat()}.json"
    out_path.write_text(str(payload))
    logger.info("Saved exchange rate snapshot to %s", out_path)
    return rate


def main():
    claims_df = extract_claims_csv()
    rate = extract_exchange_rate()
    logger.info(
        "Extraction complete: %d claims rows, USD->EUR rate = %.4f",
        len(claims_df), rate,
    )


if __name__ == "__main__":
    main()