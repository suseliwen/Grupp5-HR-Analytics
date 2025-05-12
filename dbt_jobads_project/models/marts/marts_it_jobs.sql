WITH 
    fct_job_ads AS (SELECT * FROM {{ ref('fct_job_ads') }}),
    dim_job_details AS (SELECT * FROM {{ ref('dim_job_details') }}),
    dim_occupation AS (SELECT * FROM {{ ref('dim_occupation') }}),
    dim_employer AS (SELECT * FROM {{ ref('dim_employer') }}),
    dim_aux AS (SELECT * FROM {{ ref('dim_aux') }})

SELECT
    jd.headline,
    e.employer_name,
    f.vacancies,
    f.relevance,
    o.occupation,
    o.occupation_group,
    o.occupation_field,
    f.application_deadline,
    jd.description,
    jd.duration,
    jd.salary_type,
    jd.description_html_formatted,
    jd.employment_type,
    e.employer_workplace,
    e.workplace_region,
    a.driving_license_required,
    a.own_car_required,
    a.experience_required
FROM fct_job_ads f
LEFT JOIN dim_job_details jd ON f.job_details_id = jd.job_details_id
LEFT JOIN dim_occupation o ON f.occupation_id = o.occupation_id
LEFT JOIN dim_employer e ON f.employer_id = e.employer_id
LEFT JOIN dim_aux a ON f.auxiliary_attributes_id = a.auxiliary_attributes_id
WHERE o.occupation_field = 'Yrken med teknisk inriktning'