-- The dbt test will fail if the result contains rows.
-- First CTE (test_data)
WITH test_data AS (
    SELECT 
        id,
        workplace_address__municipality,
        employer__workplace,
        {{ dbt_utils.generate_surrogate_key(['employer__workplace', 'workplace_address__municipality']) }} AS expected_key
    FROM {{ ref('src_job_ads') }}
),
-- Second CTE (dim_data):
dim_data AS (
    SELECT
        employer_id,
        workplace_municipality,
        employer_workplace
    FROM {{ ref('dim_employer') }}
)
-- Main SELECT and JOIN
SELECT
    t.id,
    t.workplace_address__municipality,
    t.employer__workplace,
    t.expected_key,
    d.employer_id
FROM test_data t
JOIN dim_data d
    ON t.workplace_address__municipality = d.workplace_municipality
    AND t.employer__workplace = d.employer_workplace
WHERE t.expected_key != d.employer_id

-- This query is typically used as a data validation or test to ensure consistency 
-- between two tables (e.g., ensuring that the keys generated in the source match the IDs in the dimension table).
