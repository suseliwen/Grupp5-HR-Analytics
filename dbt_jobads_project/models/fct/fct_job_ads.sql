WITH job_ads AS (SELECT * FROM {{ source('job_ads', 'stg_ads') }})

select
    {{ dbt_utils.generate_surrogate_key(['occupation__label']) }} AS occupation_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} AS job_details_id,
    {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} AS employer_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} AS auxiliary_attributes_id,
    
    number_of_vacancies as vacancies,
    relevance,
    application_deadline
from job_ads