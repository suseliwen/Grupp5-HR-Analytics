with dim_aux as (select * from {{ ref('src_aux') }})

select
    {{ dbt_utils.generate_surrogate_key(['driving_license_required', 'own_car_required', 'experience_required']) }} as auxiliary_attributes_id,
    driving_license_required,
    own_car_required,
    experience_required
from dim_aux
