{{
    config(
        unique_key=['event_id', 'event_ts'],
        incremental_strategy='merge',
    )
}}

select
    event_id,
    event_ts,
    wiki,
    domain,
    change_type,
    namespace,
    title,
    page_key,
    user_name,
    is_bot,
    is_anonymous,
    is_minor,
    comment,
    length_old,
    length_new,
    bytes_delta,
    is_revert,
    inserted_at
from {{ ref('stg_recentchange') }}

{% if is_incremental() %}
where event_ts > (
    select coalesce(max(event_ts) - interval '1 hour', '1970-01-01'::timestamptz)
    from {{ this }}
)
{% endif %}
