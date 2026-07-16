select
    date_trunc('day', event_ts)::date as edit_date,
    wiki,
    title,
    page_key,
    count(*)::bigint as edit_count
from {{ ref('fct_edits') }}
group by 1, 2, 3, 4
