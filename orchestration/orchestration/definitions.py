
from dagster import Definitions, load_assets_from_modules
from orchestration import assets
from dagster import define_asset_job, AssetSelection, ScheduleDefinition

# Load all @asset-decorated functions from the assets module
all_assets = load_assets_from_modules([assets])

# Define a job that includes all assets
pipeline_job = define_asset_job(
    name ="job_ads_pipeline",
    selection = AssetSelection.assets("load_job_ads_asset", "run_dbt_transformations"),
)

# Define a schedule to run the job daily at midnight
daily_schedule = ScheduleDefinition(
    job_name=pipeline_job.name,

    cron_schedule="0 9,16 * * *",  # Every day at midnight
)

# Create a Definitions object to encapsulate the assets, job, and schedule
defs = Definitions(
    assets=all_assets,
    jobs=[pipeline_job],
    schedules=[daily_schedule],
)

