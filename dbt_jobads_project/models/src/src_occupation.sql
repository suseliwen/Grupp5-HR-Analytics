with stg_job_ads as (select * from {{ source('job_ads', 'stg_ads') }}) 
      
    
    select distinct
        occupation__concept_id as occupation_id,
        occupation__label as occupation,
        occupation__legacy_ams_taxonomy_id,
        occupation_group__concept_id as occupation_group_id,
        occupation_group__label as occupation_group,
        occupation_group__legacy_ams_taxonomy_id,
        occupation_field__concept_id as occupation_field_id,
        occupation_field__label as occupation_field,
        occupation_field__legacy_ams_taxonomy_id

    from stg_job_ads


   
   
  
 
    
 
  