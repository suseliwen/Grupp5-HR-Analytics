"""
This script loads data (job ads) from the JobTech API into a DLT pipeline, and saves the ads into a DuckDB database.
It handles API-pagination, filters results by specified occupation fields, and organizes the data under a staging dataset.
"""

import config
import dlt
import requests
import json
from pathlib import Path
import os
from datetime import datetime

# Sätt rätt databasväg (test eller produktion)
if config.USE_TEST_DB:
    db_path = config.TEST_DB_PATH
else:
    db_path = config.PROD_DB_PATH

# Sends a GET-request to the URL, with specified parameters and headers.
# Raises an exception if the request fails.
# Returns the response content, decoded from JSON, into a Python dictionary.
def _get_ads(url_for_search, params):
    headers = {"accept": "application/json"}
    response = requests.get(url_for_search, headers=headers, params=params)
    response.raise_for_status()  
    return json.loads(response.content.decode("utf8"))

# Loads data (job ads) from the specified URL into a DLT-pipeline.
# The function is a DLT resource, which means it can be used to load data into a DLT pipeline.
@dlt.resource(
    primary_key="id",
    write_disposition="merge"  # Use "merge" to update existing ids and insert new ones.
)
def jobsearch_resource(params):
    url = "https://jobsearch.api.jobtechdev.se"
    url_for_search = f"{url}/search"
    limit = params.get("limit", 100)
    offset = 0

    while True:        
        page_params = dict(params, offset=offset)
        data = _get_ads(url_for_search, page_params)

        hits = data.get("hits", [])
        if not hits:            
            break

        for ad in hits:
            ad["ingestion_timestamp"] = datetime.now().isoformat()
            yield ad

        if len(hits) < limit or offset > 1900:
            break

        offset += limit

# Creates and runs a DLT pipeline to load job ads for specified occupation fields.
def run_pipeline(query, table_name, occupation_fields):
    pipeline = dlt.pipeline(
        pipeline_name="jobads_project",
        destination=dlt.destinations.duckdb(db_path),  # Använd db_path
        dataset_name="staging",
    )

    for occupation_field in occupation_fields:
        params = {"q": query, "limit": 100, "occupation-field": occupation_field}
        load_info = pipeline.run(
            jobsearch_resource(params=params),
            table_name=table_name
        )
        print(f"Occupation field: {occupation_field}")
        print(load_info)

if __name__ == "__main__":
    working_directory = Path(__file__).parent
    os.chdir(working_directory)

    query = ""
    table_name = "job_ads"
    occupation_fields = ("GazW_2TU_kJw", "6Hq3_tKo_V57", "bh3H_Y3h_5eD")

    run_pipeline(query, table_name, occupation_fields)
