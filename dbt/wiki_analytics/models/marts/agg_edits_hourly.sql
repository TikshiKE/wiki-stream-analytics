{{
    config(
        unique_key=['hour_ts', 'wiki'],
        incremental_strategy='merge',
    )
}}

with filtered as (
    select *
    from {{ ref('fct_edits') }}
    {% if is_incremental() %}
    where event_ts >= (
        select coalesce(max(hour_ts) - interval '2 hours', '1970-01-01'::timestamptz)
        from {{ this }}
    )
    {% endif %}
),

hourly as (
    select
        date_trunc('hour', event_ts) as hour_ts,
        wiki,
        count(*)::bigint as edit_count,
        count(distinct user_name)::bigint as unique_editors,
        count(*) filter (where is_bot)::numeric / nullif(count(*), 0) as bot_share,
        count(*) filter (where is_anonymous)::numeric / nullif(count(*), 0) as anonymous_share,
        coalesce(sum(bytes_delta), 0)::bigint as total_bytes_delta,
        count(*) filter (where is_revert)::bigint as revert_count
    from filtered
    group by 1, 2
)

select * from hourly
