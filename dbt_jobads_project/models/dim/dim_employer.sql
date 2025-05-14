WITH dim_employer AS (SELECT * FROM {{ ref('src_employer') }})
SELECT {{ dbt_utils.generate_surrogate_key(['employer_name', 'employer_workplace', 'workplace_municipality']) }} AS employer_id, 
    COALESCE (employer_name, 'Ingen data') AS employer_name,
    COALESCE (employer_workplace, 'Ingen data') AS employer_workplace,
    COALESCE (employer_organization_number, 'Ingen data') AS employer_organization_number,
    COALESCE (workplace_street_address, 'Ingen data') AS workplace_street_address,
    COALESCE (workplace_region, 'Ingen data') AS workplace_region,
    COALESCE (workplace_postcode, 'Ingen data') AS workplace_postcode,
    COALESCE (workplace_city, 'Ingen data') AS workplace_city,
    COALESCE (workplace_country, 'Ingen data') AS workplace_country,
    COALESCE (workplace_municipality, 'Ingen data') AS workplace_municipality
    
FROM dim_employer WHERE employer_id IS NOT NULL