with wikis as (
    select distinct
        wiki,
        domain
    from {{ ref('stg_recentchange') }}
),

enriched as (
    select
        wiki,
        domain,
        case
            when domain = 'commons.wikimedia.org' then null
            when domain in ('www.wikidata.org', 'wikidata.org', 'meta.wikimedia.org') then null
            else split_part(domain, '.', 1)
        end as language_code,
        case
            when domain like '%.wikipedia.org' then 'wikipedia'
            when domain like '%.wiktionary.org' then 'wiktionary'
            when domain like '%.wikinews.org' then 'wikinews'
            when domain like '%.wikibooks.org' then 'wikibooks'
            when domain like '%.wikiquote.org' then 'wikiquote'
            when domain like '%.wikisource.org' then 'wikisource'
            when domain like '%.wikivoyage.org' then 'wikivoyage'
            when domain in ('www.wikidata.org', 'wikidata.org') then 'wikidata'
            when domain = 'commons.wikimedia.org' then 'commons'
            when domain = 'meta.wikimedia.org' then 'meta'
            else 'other'
        end as project
    from wikis
)

select * from enriched
