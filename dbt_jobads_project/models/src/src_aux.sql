with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }}) 

select distinct 
    driving_license_required, 
    access_to_own_car as own_car_required,
    experience_required,
    working_hours_type__label as working_hours_type,
    working_hours_type__concept_id as working_hours_type_id,
    duration__label as duration,
    duration__concept_id as duration_id,
    duration__legacy_ams_taxonomy_id as duration_legacy_ams_taxonomy_id

from stg_job_ads








