"""
load.py — Load the transformed insurance claims data into Snowflake.

Reads the processed CSVs from data/processed/ (produced by transform.py) and
loads them into the INSURANCE_ETL.ANALYTICS schema using write_pandas, which
handles staging and bulk COPY INTO under the hood, and infers column types
automatically from the DataFrame.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TARGET_SCHEMA = "ANALYTICS"


def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=TARGET_SCHEMA,
    )


def load_table(conn, df: pd.DataFrame, table_name: str):
    """Create/replace a table matching the DataFrame's schema and bulk-load it."""
    df = df.copy()
    df.columns = [c.upper() for c in df.columns]

    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name,
        auto_create_table=True,
        overwrite=True,
    )
    logger.info(
        "Loaded %d rows into %s.%s (success=%s)",
        nrows, TARGET_SCHEMA, table_name, success,
    )


def main():
    claims_df = pd.read_csv(PROCESSED_DIR / "claims_enriched.csv")
    summary_df = pd.read_csv(PROCESSED_DIR / "region_summary.csv")

    conn = get_connection()
    try:
        load_table(conn, claims_df, "CLAIMS_ENRICHED")
        load_table(conn, summary_df, "REGION_SUMMARY")
    finally:
        conn.close()

    logger.info("Load complete.")


if __name__ == "__main__":
    main()