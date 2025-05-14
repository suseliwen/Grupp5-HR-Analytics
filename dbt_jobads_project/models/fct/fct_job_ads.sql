WITH job_ads AS (
    SELECT * FROM {{ ref('src_job_ads') }}    
),

dim_aux AS (
    SELECT * FROM {{ ref('dim_aux') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['job_ads.occupation__label']) }} AS occupation_id,
    {{ dbt_utils.generate_surrogate_key(['job_ads.id']) }} AS job_details_id,
    {{ dbt_utils.generate_surrogate_key(['job_ads.employer__workplace', 'job_ads.employer__name', 'workplace_municipality']) }} AS employer_id,
    dim_aux.auxiliary_attributes_id,
    vacancies,
    relevance,
    application_deadline
FROM job_ads
LEFT JOIN dim_aux
    ON job_ads.driving_license_required = dim_aux.driving_license_required
   AND job_ads.own_car_required = dim_aux.own_car_required
   AND job_ads.experience_required = dim_aux.experience_required