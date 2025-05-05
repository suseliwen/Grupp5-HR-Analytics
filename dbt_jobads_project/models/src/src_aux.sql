-- This model extracts auxiliary job attributes from the job ads source.
-- Boolean columns are kept in their native format; no nulls are replaced.

with stg_job_ads as (
    select * from {{ source('job_ads', 'stg_ads') }}
)

select distinct
    driving_license_required,
    access_to_own_car as own_car_required,
    experience_required
from stg_job_ads







