
from dagster import Definitions, load_assets_from_modules
from orchestration import assets  

# Load all @asset-decorated functions from the assets module
all_assets = load_assets_from_modules([assets]) 

# Define the Dagster Definitions object with the loaded assets
defs = Definitions(
    assets=all_assets,
)