-- CI seed data: small sample of edit events for dbt build in GitHub Actions.
-- Timestamps are relative to CURRENT_TIMESTAMP so partitions stay valid.

INSERT INTO raw.recentchange (
    event_id, event_ts, wiki, domain, change_type, namespace, title,
    user_name, is_bot, is_anonymous, is_minor, comment, length_old, length_new
) VALUES
    (
        '11111111-1111-1111-1111-111111111101',
        date_trunc('hour', CURRENT_TIMESTAMP) - interval '3 hours',
        'enwiki', 'en.wikipedia.org', 'edit', 0, 'Earth',
        'Alice', false, false, false, 'fix typo', 100, 105
    ),
    (
        '11111111-1111-1111-1111-111111111102',
        date_trunc('hour', CURRENT_TIMESTAMP) - interval '2 hours',
        'enwiki', 'en.wikipedia.org', 'edit', 0, 'Moon',
        'Bob', false, false, true, 'minor fix', 200, 201
    ),
    (
        '11111111-1111-1111-1111-111111111103',
        date_trunc('hour', CURRENT_TIMESTAMP) - interval '1 hour',
        'ruwiki', 'ru.wikipedia.org', 'new', 0, 'Марс',
        '127.0.0.1', false, true, false, 'new article', null, 500
    ),
    (
        '11111111-1111-1111-1111-111111111104',
        date_trunc('hour', CURRENT_TIMESTAMP) - interval '30 minutes',
        'enwiki', 'en.wikipedia.org', 'edit', 0, 'Sun',
        'BotEditor', true, false, false, 'bot cleanup', 300, 295
    ),
    (
        '11111111-1111-1111-1111-111111111105',
        CURRENT_TIMESTAMP - interval '5 minutes',
        'dewiki', 'de.wikipedia.org', 'edit', 0, 'Berlin',
        'Carol', false, false, false, 'update stats', 400, 420
    )
ON CONFLICT (event_id, event_ts) DO NOTHING;
