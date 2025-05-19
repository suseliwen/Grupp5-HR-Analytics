
with
   dim_occupation as (select * from {{ ref('dim_occupation') }}),
   fct_job_ads as (select * from {{ ref('fct_job_ads') }})

select
    any_value(fct.job_details_id) as job_id,
    occ.occupation_field,
    occ.occupation,
    count(*) as antal_annons
from refined.fct_job_ads fct
left join refined.dim_occupation occ
    on fct.occupation_id = occ.occupation_id
where occ.occupation_field = 'Yrken med social inriktning'
group by occ.occupation_field, occ.occupation
order by antal_annons desc
