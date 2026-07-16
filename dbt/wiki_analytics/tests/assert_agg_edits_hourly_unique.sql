-- Composite uniqueness: one row per hour and wiki.
select hour_ts, wiki, count(*) as n
from {{ ref('agg_edits_hourly') }}
group by 1, 2
having count(*) > 1
