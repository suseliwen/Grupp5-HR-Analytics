


WITH stg_job_ads AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY id 
               ORDER BY application_deadline DESC
           ) AS rn
    FROM {{ source('job_ads', 'stg_ads') }}
)

SELECT
    id,
    occupation__label,
    publication_date,  
    number_of_vacancies AS vacancies,
    relevance,
    application_deadline,
    driving_license_required,
    access_to_own_car AS own_car_required,
    experience_required,
    employer__name,
    employer__workplace,
    workplace_address__municipality 
FROM stg_job_ads
WHERE rn = 1