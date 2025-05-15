
select *, 'Yrken med social inriktning' as occupation_field
from {{ ref('mart_occupation_social')}}

union all

select *, 'Yrken med teknisk inriktning' as occupation_field
from {{ ref('mart_it_jobs')}}

union all

select *,  'Chefer och verksamhetsledare' as occupation_field
from {{ ref('mart_leadership_jobs')}}