-- Composite uniqueness: one row per day and page.
select edit_date, page_key, count(*) as n
from {{ ref('mart_top_pages_daily') }}
group by 1, 2
having count(*) > 1
