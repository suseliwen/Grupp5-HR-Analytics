WITH job_details AS (SELECT * FROM {{ ref('src_job_details') }})

SELECT
    {{ dbt_utils.generate_surrogate_key(['id']) }} AS job_details_id,
    COALESCE (headline, 'Ingen data') AS headline,
    CAST(publication_date AS DATE) AS publication_date,
    COALESCE (description, 'Ingen data') AS description,
    COALESCE (description_html_formatted, 'Ingen data') AS description_html_formatted,
    COALESCE (application_url, 'Ingen data') AS application_url,
    COALESCE (employment_type, 'Ingen data') AS employment_type,
    COALESCE(duration, 'Ingen data') AS duration,
    COALESCE (salary_type, 'Ingen data') AS salary_type,
    CASE WHEN scope_of_work_min IS NULL THEN 'Ingen data' 
     ELSE CAST(scope_of_work_min AS STRING) END AS scope_of_work_min,
    CASE WHEN scope_of_work_max IS NULL THEN 'Ingen data' 
     ELSE CAST(scope_of_work_max AS STRING) END AS scope_of_work_max
FROM job_details
WHERE id IS NOT NULL