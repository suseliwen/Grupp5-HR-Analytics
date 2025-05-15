WITH job_ads AS (
    SELECT * FROM {{ ref('src_job_ads') }}    
)

SELECT

    {{ dbt_utils.generate_surrogate_key(['occupation__label']) }} AS occupation_id,
    {{ dbt_utils.generate_surrogate_key(['id']) }} AS job_details_id,
    {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} AS employer_id,
    {{ dbt_utils.generate_surrogate_key(['driving_license_required', 'own_car_required', 'experience_required']) }} AS auxiliary_attributes_id,
    vacancies,
    relevance,
    application_deadline
FROM job_ads