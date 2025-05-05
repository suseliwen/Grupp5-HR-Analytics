-- This model is used to extract the occupation data from the job ads source table.
with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }}) 
      
    -- Coalesce is used to handle null values and replace them with 'Ingen data'.
    -- This is useful to ensure that the final output does not contain any null values.
   select distinct
    occupation__concept_id as occupation_id,
    coalesce(occupation__label, 'Ingen data') as occupation,
    coalesce(occupation__legacy_ams_taxonomy_id, 'Ingen data') as occupation_legacy_id,

    coalesce(occupation_group__concept_id, 'Ingen data') as occupation_group_id,
    coalesce(occupation_group__label, 'Ingen data') as occupation_group,
    coalesce(occupation_group__legacy_ams_taxonomy_id, 'Ingen data') as occupation_group_legacy_id,

    coalesce(occupation_field__concept_id, 'Ingen data') as occupation_field_id,
    coalesce(occupation_field__label, 'Ingen data') as occupation_field,
    coalesce(occupation_field__legacy_ams_taxonomy_id, 'Ingen data') as occupation_field_legacy_id

from stg_job_ads


   
   
  
 
    
 
  