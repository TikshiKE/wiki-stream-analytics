with classified as (
    select
        date_trunc('day', event_ts)::date as edit_date,
        case
            when is_bot then 'bot'
            when is_anonymous then 'anonymous'
            else 'registered'
        end as editor_type
    from {{ ref('fct_edits') }}
)

select
    edit_date,
    editor_type,
    count(*)::bigint as edit_count
from classified
group by 1, 2
