WITH stg_job_ads AS (SELECT * FROM {{ source('job_ads', 'stg_ads') }})
SELECT id, 
    employer__name as employer_name, 
    employer__workplace as employer_workplace, 
    employer__organization_number as employer_organization_number,
    workplace_adress__street_adress as workplace_street_adress,
    workplace__adress_region as workplace_region,
    workplace_adress__postcode as workplace_postcode,
    workplace_adress__city as workplace_city,
    workplace_adress__country as workplace_country
FROM stg_job_ads