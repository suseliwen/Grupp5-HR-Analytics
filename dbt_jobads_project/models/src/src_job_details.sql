WITH stg_job_ads AS (SELECT * FROM {{ source('job_ads', 'stg_ads') }})

SELECT
    id,
    headline,
    description__text AS description,
    description__text_formatted AS description_html,
    duration__label AS duration,
    salary_type__label AS salary_type,
    salary_description,
    working_hours_type__label AS working_hours_type__label,
    scope_of_work__min AS scope_of_work_min,
    scope_of_work__max AS scope_of_work_max
FROM stg_job_ads
