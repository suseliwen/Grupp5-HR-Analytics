
-- Code from lesson
with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }})

select
    id,
    occupation__label,    
    number_of_vacancies as vacancies,
    relevance,
    application_deadline,
    driving_license_required,
    access_to_own_car as own_car_required,
    experience_required,
    employer__name,
    employer__workplace,
    workplace_address__municipality 
from stg_job_ads