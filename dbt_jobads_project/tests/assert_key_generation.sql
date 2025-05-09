-- The dbt test will fail if the result contains rows.
-- First CTE (test_data)
WITH test_data AS (
    SELECT 
        id,
        employer_name,
        employer_workplace,
        {{ dbt_utils.generate_surrogate_key(['employer_name', 'employer_workplace']) }} AS expected_key
    FROM {{ ref('src_employer') }}
),
-- Second CTE (dim_data):
dim_data AS (
    SELECT
        employer_id,
        employer_name,
        employer_workplace
    FROM {{ ref('dim_employer') }}
)
-- Main SELECT and JOIN
SELECT
    t.id,
    t.employer_name,
    t.employer_workplace,
    t.expected_key,
    d.employer_id
FROM test_data t
JOIN dim_data d
    ON t.employer_name = d.employer_name
    AND t.employer_workplace = d.employer_workplace
WHERE t.expected_key != d.employer_id

-- This query is typically used as a data validation or test to ensure consistency 
-- between two tables (e.g., ensuring that the keys generated in the source match the IDs in the dimension table).
