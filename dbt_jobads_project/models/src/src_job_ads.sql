
-- Code from lesson 7/data-engineering-OPA240-2023/lesson_7/dbt_jobads_project/models/src/src_job_ads.sql
with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }})

select
    occupation__label,
    id,
    employer__workplace,
    workplace_address__municipality,
    number_of_vacancies as vacancies,
    relevance,
    application_deadline
from stg_job_ads