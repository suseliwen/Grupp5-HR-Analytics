WITH job_details AS (SELECT * FROM {{ ref('src_job_details') }})

SELECT
    {{ dbt_utils.generate_surrogate_key(['id']) }} AS job_details_id,
    headline,
    description,
    description_html_formatted,
    employment_type,
    COALESCE(duration, 'Ingen data') AS duration,
    salary_type,
    CASE WHEN scope_of_work_min IS NULL THEN 'Ingen data' 
     ELSE CAST(scope_of_work_min AS STRING) END AS scope_of_work_min,
    CASE WHEN scope_of_work_max IS NULL THEN 'Ingen data' 
     ELSE CAST(scope_of_work_max AS STRING) END AS scope_of_work_max
FROM job_details