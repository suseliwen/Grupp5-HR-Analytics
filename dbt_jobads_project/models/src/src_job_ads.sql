
-- Code from lesson
with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }})

select
    occupation__label,
    id,
    employer__workplace,
    workplace_address__municipality,
    number_of_vacancies as vacancies,
    relevance,
    application_deadline,
    driving_license_required,
    access_to_own_car as own_car_required,
    experience_required
from stg_job_ads