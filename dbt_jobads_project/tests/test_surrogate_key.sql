-- fact_keys CTE (Common Table Expression)
WITH fact_keys AS (
    SELECT
        id,
        {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} AS expected_key
    FROM {{ ref('src_job_ads') }}
),
-- dim_keys CTE
dim_keys AS (
    SELECT
        employer_id
    FROM {{ ref('dim_employer') }}
)
-- Main Query (Comparison)
SELECT 
    f.id,
    f.expected_key
FROM fact_keys f
LEFT JOIN dim_keys d
    ON f.expected_key = d.employer_id
WHERE d.employer_id IS NULL

-- The query checks if there are any discrepancies between the surrogate key (employer_id) 
-- generated from the fact table and the actual employer_id in the dimension table.

