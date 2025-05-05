-- This model extracts auxiliary job attributes from the job ads source.
-- Null values are handled using COALESCE to ensure clean, consistent data.

with stg_job_ads as (
    select * from {{ source('job_ads', 'stg_ads') }}
)

select distinct
    coalesce(driving_license_required, 'Ingen data') as driving_license_required,
    coalesce(access_to_own_car, 'Ingen data') as own_car_required,
    coalesce(experience_required, 'Ingen data') as experience_required
from stg_job_ads







