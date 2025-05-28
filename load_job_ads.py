
"""
This script loads data (job ads) from the JobTech API into a DLT pipeline, and saves the ads into a DuckDB database.
It handles API-pagination, filters results by specified occupation fields, and organizes the data under a staging dataset.
"""
import dlt
import requests
import json
from pathlib import Path
import os
import duckdb
from datetime import datetime

# Function to fetch distinct IDs from the DuckDB database.
# This is used to avoid duplicate entries when loading data.
def get_existing_ids():
    try:
        con = duckdb.connect("jobads_data_warehouse.duckdb")
        result = con.execute("SELECT DISTINCT id FROM job_ads").fetchall()
        con.close()
        return {row[0] for row in result}
    except Exception as e:
        print(f"Error fetching existing IDs: {e}")
        return set()

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
@dlt.resource(write_disposition="append")
def jobsearch_resource(params, existing_ids):
    # Set up API URL and pagination parameters: 'limit' defines page size, 'offset' defines starting point.
    url = "https://jobsearch.api.jobtechdev.se"
    url_for_search = f"{url}/search"
    limit = params.get("limit", 100)
    offset = 0

    while True:        
        page_params = dict(params, offset=offset)
        data = _get_ads(url_for_search, page_params)

        # Get list of job ads from response.
        hits = data.get("hits", [])
        if not hits:            
            break

        # Yield each ad from the current page and check if ad already exists in the database.
        for ad in hits:
            ad_id = ad.get("id")
            if ad_id and ad_id not in existing_ids:
                ad["ingestion_timestamp"] = datetime.now().isoformat() #To enable viualization of the latest data ingestion in the Streamlit app
                yield ad

        # If fewer ads than the limit are returned, or if the offset exceeds 1900, stop fetching.
        if len(hits) < limit or offset > 1900:
            break

        offset += limit

# Creates and runs a DLT pipeline to load job ads for specified occupation fields.
# The pipeline is configured to write to a DuckDB database.
def run_pipeline(query, table_name, occupation_fields):
    pipeline = dlt.pipeline(
        pipeline_name="jobads_project",
        destination=dlt.destinations.duckdb("jobads_data_warehouse.duckdb"),
        dataset_name="staging",
    )

    # Get existing IDs from the database to avoid duplicates.
    existing_ids = get_existing_ids()
    
    # Iterate over each occupation field and load job ads into the pipeline.
    for occupation_field in occupation_fields:
        params = {"q": query, "limit": 100, "occupation-field": occupation_field}
        load_info = pipeline.run(
            jobsearch_resource(params=params, existing_ids=existing_ids),
            table_name=table_name
        )
        print(f"Occupation field: {occupation_field}")
        print(load_info)

# Main function to execute the script.
# It sets the working directory, defines parameters, and calls the run_pipeline function.
if __name__ == "__main__":
    working_directory = Path(__file__).parent
    os.chdir(working_directory)

    query = ""
    table_name = "job_ads"

    # "Yrken med social inriktning",  "Yrken med teknisk inriktning", "Chefer och verksamhetsledare"
    occupation_fields = ("GazW_2TU_kJw", "6Hq3_tKo_V57", "bh3H_Y3h_5eD")

    run_pipeline(query, table_name, occupation_fields)