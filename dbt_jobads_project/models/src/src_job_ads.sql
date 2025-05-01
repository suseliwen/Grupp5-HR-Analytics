WITH stg_job_ads AS (SELECT * FROM {{ source('job_ads', 'stg_ads') }})

SELECT 
    occupation__label, 
    id, employer__workplace, 
    workplace_address__municipality, 
    number_of_vacancies AS vacancies, 
    relevance, 
    application_deadline
FROM stg_job_ads