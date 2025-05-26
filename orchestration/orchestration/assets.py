from dagster import asset, AssetIn
from pathlib import Path
import sys
import subprocess

# Telling Python where to find the load_job_ads module
# This is necessary because the load_job_ads.py file is located two directories up from this script.
sys.path.append(str(Path(__file__).resolve().parents[2]))

# Importing the run_pipeline function from load_job_ads.py
from load_job_ads import run_pipeline

# This code defines Dagster assets for loading job ads data
@asset
def load_job_ads_asset():
    """
     The Dagster asset, that loads job ads data into DuckDB.
    
    This asset runs the DLT pipeline defined in `load_job_ads.py`, using specified
    query parameters and occupation fields. The data is written to the 'job_ads' table
    in the 'jobads_data_warehouse.duckdb' database.
    """
    query = ""
    table_name = "job_ads"
    occupation_fields = ("GazW_2TU_kJw", "6Hq3_tKo_V57", "bh3H_Y3h_5eD")
    run_pipeline(query, table_name, occupation_fields)


# The following code defines Dagster assets for running DBT transformations. 
# The asset depends on the `load_job_ads_asset` to ensure that the job ads data is loaded before running the transformations.
@asset(deps = [load_job_ads_asset])
def run_dbt_transformations():
    """
    The Dagster asset that runs DBT transformations on the job ads data.
    
    This asset executes the DBT command to run transformations defined in the DBT project.
    It is dependent on the `load_job_ads_asset` to ensure that the job ads data is loaded before
    running the transformations.
    """
    dbt_path = Path(__file__).resolve().parents[2] / "dbt_jobads_project"
    subprocess.run(["dbt", "run", "--project-dir", str(dbt_path)], check=True)
