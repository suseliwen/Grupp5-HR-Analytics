WITH 
    fct_job_ads as (select * from {{ ref('fct_job_ads') }}),
    dim_job_details as (select * from {{ ref('dim_job_details') }}),
    dim_occupation as (select * from {{ ref('dim_occupation') }})

SELECT
    jd.headline,
    f.vacancies,
    f.relevance,
    o.occupation,
    o.occupation_group,
    o.occupation_field,
    f.application_deadline,
    jd.description,
    jd.duration,
    jd.salary_type,
    
    
FROM fct_job_ads f
LEFT JOIN dim_job_details jd ON f.job_details_id = jd.job_details_id
LEFT JOIN dim_occupation o ON f.occupation_id = o.occupation_id

WHERE o.occupation_field = 'Yrken med social inriktning'
