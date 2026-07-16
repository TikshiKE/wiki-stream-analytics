with source as (
    select * from {{ source('raw', 'recentchange') }}
),

typed as (
    select
        event_id,
        event_ts,
        wiki,
        domain,
        change_type,
        namespace,
        title,
        user_name,
        coalesce(is_bot, false) as is_bot,
        coalesce(is_anonymous, false) as is_anonymous,
        coalesce(is_minor, false) as is_minor,
        comment,
        length_old,
        length_new,
        inserted_at,
        length_new - length_old as bytes_delta,
        coalesce(comment, '') ~* '{{ var("revert_pattern") }}' as is_revert,
        wiki || ':' || coalesce(title, '') as page_key
    from source
    where change_type in ('edit', 'new')
)

select * from typed
