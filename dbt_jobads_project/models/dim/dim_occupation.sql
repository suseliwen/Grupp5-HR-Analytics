-- Create a temporary table (CTE) to store the occupation data from the source table
with dim_occupation as (
    select * from {{ ref('src_occupation') }})

-- Build the final occupation dimension table by selecting distinct values from the temporary table
-- and generating a surrogate key for the occupation
    select
    {{ dbt_utils.generate_surrogate_key(['occupation']) }} as occupation_id,
    max (occupation) as occupation, 
    max(occupation_group) as occupation_group, -- get a representative group for each occupation
    max(occupation_field) as occupation_field -- get a representative field for each occupation
from dim_occupation
group by occupation -- group by occupation to ensure unique values



