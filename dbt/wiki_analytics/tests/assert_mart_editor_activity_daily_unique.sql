-- Composite uniqueness: one row per day and editor type.
select edit_date, editor_type, count(*) as n
from {{ ref('mart_editor_activity_daily') }}
group by 1, 2
having count(*) > 1
