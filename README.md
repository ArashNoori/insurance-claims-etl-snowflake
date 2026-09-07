# Insurance Claims ETL Pipeline

An end-to-end ETL pipeline that extracts insurance claims data and live currency exchange rates, transforms and enriches them, and loads the results into Snowflake for analysis.

## Overview

This project was built to apply data engineering fundamentals to a realistic, insurance-domain dataset while transitioning from backend software development into data engineering. It demonstrates two common extraction patterns (file-based and API-based), data cleaning and enrichment, and a production-style load into a cloud data warehouse.

## Architecture

Insurance claims CSV (public source) + Live USD to EUR rate (Frankfurter API)
|
v
src/extract.py -> data/raw/ (bronze layer)
|
v
src/transform.py -> clean, deduplicate, convert to EUR,
derive risk segments, aggregate
|
v
data/processed/ (silver layer)
|
v
src/load.py
|
v
Snowflake (INSURANCE_ETL.ANALYTICS) - CLAIMS_ENRICHED - REGION_SUMMARY

## Tech stack

- Python — pandas for transformation, requests for API extraction
- Snowflake — cloud data warehouse (load target)
- snowflake-connector-python — bulk loading via write_pandas
- Git/GitHub — version control

## Data sources

1. Insurance claims (CSV) — US Medical Insurance Costs dataset — https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/insurance.csv — 1,338 records (age, sex, BMI, smoker status, region, charges)
2. Exchange rates (API) — Frankfurter API — https://frankfurter.dev/ — live USD to EUR rate, used to normalize claim charges to EUR

## What the pipeline does

1. Extract (src/extract.py) — pulls both raw sources and saves them unmodified to data/raw/
2. Transform (src/transform.py) — deduplicates and validates records, converts charges to EUR, derives a risk_segment (low/medium/high, based on smoker status and BMI), and builds a region-level summary
3. Load (src/load.py) — bulk-loads the processed tables into Snowflake (INSURANCE_ETL.ANALYTICS schema), auto-creating tables that match the DataFrame schema

## Sample finding

Across every region, smokers show 3-4x higher average claim charges than non-smokers — consistent with expected risk patterns in health insurance data, and a sanity check that the pipeline's transformations are producing sound output.

## Running it locally

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Add your own Snowflake credentials to a .env file (see .env.example)

python src/extract.py
python src/transform.py
python src/load.py

## Project status

- [x] Extract from file + API sources
- [x] Transform: cleaning, enrichment, aggregation
- [x] Load into Snowflake
- [ ] Orchestration with Apache Airflow
- [ ] Automated data quality tests
- [ ] CI pipeline

This project is actively being developed as part of my transition into data engineering.

## Author

Sadeq (Arash) Noori Nooghabi — https://linkedin.com/in/arashnoori91
