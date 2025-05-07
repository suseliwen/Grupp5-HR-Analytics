WITH stg_job_ads AS (SELECT * FROM {{ source('job_ads', 'stg_ads') }})
SELECT id, 
    employer__name as employer_name, 
    employer__workplace as employer_workplace, 
    employer__organization_number as employer_organization_number,
    workplace_address__street_address as workplace_street_address,
    workplace_address__region as workplace_region,
    workplace_address__postcode as workplace_postcode,
    workplace_address__city as workplace_city,
    workplace_address__country as workplace_country
FROM stg_job_ads