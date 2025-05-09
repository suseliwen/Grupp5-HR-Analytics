-- fact_keys CTE (Common Table Expression)
WITH fact_keys AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['job_ads.employer__name', 'job_ads.employer__workplace']) }} AS employer_id,
        employer__name,
        employer__workplace
    FROM {{ ref('src_job_ads') }} AS job_ads
    GROUP BY employer__name, employer__workplace
),
-- dim_keys CTE
dim_keys AS (
    SELECT
        employer_id,
        employer_name,
        employer_workplace
    FROM {{ ref('dim_employer') }}
)
-- Main Query (Comparison)
SELECT
    f.employer__name,
    f.employer__workplace,
    f.employer_id AS fact_employer_id,
    d.employer_id AS dim_employer_id
FROM fact_keys f
FULL OUTER JOIN dim_keys d
    ON f.employer__name = d.employer_name
    AND f.employer__workplace = d.employer_workplace
WHERE f.employer_id != d.employer_id
   OR f.employer_id IS NULL
   OR d.employer_id IS NULL

-- The query checks if there are any discrepancies between the surrogate key (employer_id) 
-- generated from the fact table and the actual employer_id in the dimension table. 