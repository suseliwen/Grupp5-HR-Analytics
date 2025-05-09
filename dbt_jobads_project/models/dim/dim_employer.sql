WITH dim_employer AS (SELECT * FROM {{ ref('src_employer') }})
SELECT {{ dbt_utils.generate_surrogate_key(['employer_name', 'employer_workplace']) }} AS employer_id, 
    employer_name, 
    employer_workplace, 
    employer_organization_number,
    workplace_street_address,
    workplace_region,
    workplace_postcode,
    workplace_city,
    workplace_country
FROM dim_employer