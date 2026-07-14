# PROMPTS — готовые промты для агента по этапам

Как пользоваться: открываешь новый чат с агентом (или продолжаешь текущий), копируешь промт
нужного этапа целиком и отправляешь. Каждый промт самодостаточен: агент сначала читает PLAN.md,
потом делает этап и проверяет результат по критериям.

---

## Общее правило для всех этапов

Каждый промт начинается с этого блока (он уже включён в каждый промт ниже):

> Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
> Сначала прочитай PLAN.md в корне проекта целиком: там архитектура, модель данных,
> зафиксированные технические решения (версии, библиотеки) и критерии готовности этапов.
> Строго следуй зафиксированным решениям, не пересматривай их без крайней необходимости.
> Работай в feature-ветке `stage-N-<название>`, коммить логическими шагами.
> В конце этапа: прогони все тесты и линтер, проверь критерий «Готово, когда» из PLAN.md,
> отметь чекбоксы этапа в PLAN.md, покажи мне итог и что проверить руками.

---

## Этап 0 — скелет репозитория

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.

Задача — Этап 0: скелет репозитория и локальная инфраструктура.

1. Инициализируй git-репозиторий, создай структуру папок из раздела 5 PLAN.md
   (пустые пакеты сервисов с заглушками, чтобы структура была видна).
2. Создай .gitignore (Python, dbt, Airflow, .env, IDE), .env.example со ВСЕМИ переменными,
   которые понадобятся проекту (Kafka, Postgres, Redis, Telegram — с комментариями),
   README-заглушку с названием и одним абзацем описания, лицензию MIT.
3. Корневой pyproject.toml: общие настройки ruff (line-length 100, включить isort-правила)
   и pytest. В каждом сервисе — свой pyproject.toml с зависимостями через uv.
4. docker-compose.yml для локальной разработки: Kafka (KRaft, один брокер,
   bitnami/apache-kafka, порт наружу для отладки), Postgres 16, Redis 7,
   Kafka UI (provectus/kafka-ui). Всем сервисам — healthcheck и depends_on по condition.
   Airflow НЕ добавляй — он появится на этапе 4.
5. .github/workflows/ci.yml: job lint (ruff check + ruff format --check) и job test (pytest;
   пока пустые тесты-заглушки, чтобы pipeline был зелёным). Триггеры: PR и push в main.
6. Проверь: docker compose up -d поднимает всё здоровым (docker compose ps), Kafka UI
   открывается на localhost.
7. Скажи мне, когда создавать репозиторий на GitHub — попрошу тебя запушить или сделаю сам.

Учитывай: я на Windows, Docker Desktop установлен. Все команды давай под PowerShell.
В конце: тесты и линтер зелёные, чекбоксы Этапа 0 в PLAN.md отмечены, короткий итог.
```

---

## Этап 1 — producer

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-1-producer.

Задача — Этап 1: сервис producer (services/producer), который читает Wikimedia EventStreams
и пишет в Kafka.

Требования:
1. SSE-клиент на httpx + httpx-sse: стрим https://stream.wikimedia.org/v2/stream/recentchange,
   заголовок User-Agent с названием проекта и контактом (требование Wikimedia),
   reconnect с Last-Event-ID и экспоненциальным backoff (1s → 60s max, с джиттером).
2. Валидация события pydantic-моделью (поля — по разделу 2 PLAN.md). Невалидный JSON или
   событие без meta.id → в топик wiki.recentchange.dlq с причиной в заголовке сообщения.
3. Продюсер confluent-kafka: топик wiki.recentchange, key = wiki, acks=all,
   enable.idempotence=true, compression=lz4. Топики создаются идемпотентно при старте
   (AdminClient): wiki.recentchange — 3 партиции, retention 24h; dlq — 1 партиция.
4. Graceful shutdown по SIGTERM/SIGINT: дочитать, flush продюсера, выйти с кодом 0.
5. Структурные логи + счётчики раз в 30 сек: событий получено/отправлено/в DLQ, реконнекты.
6. Конфиг через pydantic-settings (env: KAFKA_BOOTSTRAP_SERVERS, SSE_URL, имена топиков и т.д.).
7. Dockerfile (multi-stage, uv, non-root user), сервис добавить в docker-compose.yml.
8. Тесты (pytest): парсинг валидного/невалидного события, логика backoff, маппинг
   события в Kafka-сообщение. SSE и Kafka в юнит-тестах — моки.

Проверка: подними стек, дай команду посмотреть поток в Kafka UI; покажи логи producer
со счётчиками. В конце: тесты и линтер зелёные, чекбоксы Этапа 1 в PLAN.md отмечены,
PR-описание для ветки.
```

---

## Этап 2 — consumer + raw-слой + Redis

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-2-consumer.

Задача — Этап 2: raw-слой в Postgres, сервис consumer (services/consumer), дедуп и live-метрики
в Redis.

Требования:
1. Миграции sql/init (нумерованные .sql) + идемпотентный Python-скрипт применения
   (таблица schema_migrations, применять только новые). Миграция 001: схема raw,
   партиционированная таблица raw.recentchange точно по DDL из раздела 4 PLAN.md,
   bootstrap-партиции (сегодня + 3 дня вперёд), DEFAULT-партиция, индексы,
   read-only роль для дашборда.
2. Consumer на confluent-kafka: group pg-writer, enable.auto.commit=false.
   Пайплайн на сообщение: parse → фильтр type in (edit, new) → дедуп → буфер.
   Флаш буфера: 500 событий или 5 секунд. Порядок флаша: INSERT батча в Postgres
   (executemany, ON CONFLICT (event_id, event_ts) DO NOTHING) → INCR live-счётчиков в Redis →
   commit оффсетов. Упал INSERT — оффсеты не коммитим, батч переиграется (это безопасно).
3. Дедуп: SET dedup:{meta.id} NX EX 3600. Redis недоступен → пропускаем дедуп и пишем
   (Postgres PK защитит), пишем warning.
4. Live-счётчики: live:edits:total:{yyyymmddhhmm} и live:edits:{wiki}:{yyyymmddhhmm},
   TTL 2 часа. Вычисление is_anonymous: user_name парсится как IPv4/IPv6 (модуль ipaddress).
5. Graceful shutdown: дописать буфер, закоммитить, выйти.
6. Конфиг pydantic-settings, структурные логи со счётчиками, Dockerfile, сервис в compose
   (запуск после применения миграций — отдельный init-контейнер или entrypoint).
7. Тесты: маппинг события в строку, буфер/флаш по размеру и таймауту, дедуп с fakeredis,
   is_anonymous. Интеграционный тест (testcontainers: Kafka + Postgres + Redis):
   опубликовать 100 событий с дублями → в таблице ровно уникальные, оффсеты закоммичены.
   Интеграционные тесты пометить маркером integration, в CI пока не включать.

Проверка: подними весь стек, покажи что count(*) в raw.recentchange растёт, и что при
рестарте consumer дублей не появляется. В конце: тесты и линтер зелёные, чекбоксы Этапа 2
в PLAN.md отмечены, PR-описание.
```

---

## Этап 3 — dbt

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-3-dbt. Перед началом подними стек и дай producer/consumer поработать,
чтобы в raw были живые данные для проверки моделей.

Задача — Этап 3: dbt-проект dbt/wiki_analytics поверх raw-слоя.

Требования:
1. dbt-core + dbt-postgres, profiles.yml с подключением через env-переменные
   (профили dev — локальный Postgres, prod — Railway; target по DBT_TARGET).
2. Source raw.recentchange c freshness-чеком (warn > 10 min, error > 60 min по event_ts).
3. Модели (схемы staging и marts, materialized как указано):
   - stg_recentchange (view): типизация, bytes_delta = length_new - length_old,
     is_revert по регулярке на comment (revert|rv\b|undo|rollback|откат), page_key = wiki || ':' || title.
   - dim_wiki (table): справочник из событий — wiki, domain, язык (из domain), проект
     (wikipedia/wiktionary/commons/wikidata/прочее).
   - fct_edits (incremental, unique_key=(event_id, event_ts), инкремент по event_ts
     с lookback 1 час): грейн — одно событие.
   - agg_edits_hourly (incremental по часу, lookback 2 часа): час × вики → правки,
     уникальные редакторы, доля ботов, доля анонимов, сумма bytes_delta, реверты.
   - mart_top_pages_daily (table): день × страница, топ по числу правок.
   - mart_editor_activity_daily (table): день × тип редактора (bot/anonymous/registered) → активность.
4. Тесты: unique + not_null на ключах всех моделей, accepted_values на change_type,
   relationships fct_edits → dim_wiki, кастомный generic-тест «значение в диапазоне»
   для доли ботов (0..1). Описания всех моделей и ключевых колонок в yml.
5. dbt build должен быть идемпотентным: два запуска подряд — одинаковый результат без ошибок.
6. Добавь dbt в dev-зависимости, задокументируй в README проекта dbt как запускать локально.

Проверка: dbt build (два раза подряд), dbt docs generate; покажи мне 2-3 SELECT из витрин
с осмысленными цифрами. В конце: тесты и линтер зелёные, чекбоксы Этапа 3 в PLAN.md отмечены,
PR-описание.
```

---

## Этап 4 — Airflow

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-4-airflow.

Задача — Этап 4: оркестрация через Airflow (папка airflow/).

Требования:
1. Airflow (актуальная стабильная 2.x, LocalExecutor) в docker-compose: кастомный образ
   (airflow/Dockerfile) с установленным dbt и скопированным dbt-проектом — тот же образ
   потом поедет на Railway. Метаданные — в отдельной БД airflow_meta того же Postgres
   (добавь её создание в миграции). Веб-интерфейс на localhost:8080.
2. DAG dbt_hourly (@hourly, catchup=False, max_active_runs=1):
   task dbt_build → BashOperator 'dbt build' внутри контейнера;
   retry 2 раза с паузой 5 мин; on_failure_callback — алерт в Telegram (утилита
   airflow/plugins/alerts.py, бот-токен и chat_id из env, при отсутствии токена — просто лог).
3. DAG maintenance_daily (@daily):
   - создать партиции raw на 3 дня вперёд (идемпотентно),
   - дропнуть партиции старше RETENTION_DAYS (env, по умолчанию 14),
   - VACUUM ANALYZE витрин,
   - DQ-чеки: свежесть raw (max(event_ts) < 10 мин назад), объём за вчера в пределах
     ±60% от среднего за 7 дней; провал чека → Telegram-алерт, DAG красный.
4. Логика работы с партициями — отдельным тестируемым Python-модулем (генерация имён/границ
   партиций, вычисление какие дропать), DAG-и только вызывают его.
5. Тесты: import-тест DAG-ов (DagBag без ошибок), юнит-тесты модуля партиций и DQ-логики.
6. Не забудь: тайзмона везде UTC, у DAG-ов теги, docstring с описанием что и зачем.

Проверка: подними стек с Airflow, включи оба DAG-а, покажи успешный ручной запуск обоих;
затем останови consumer на 15 минут и покажи, что DQ-чек падает (алерт или красный таск).
В конце: тесты и линтер зелёные, чекбоксы Этапа 4 в PLAN.md отмечены, PR-описание.
```

---

## Этап 5 — дашборд

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-5-dashboard.

Задача — Этап 5: Streamlit-дашборд (dashboard/), витрина проекта для рекрутёров.

Требования:
1. Streamlit + plotly. Подключения: Postgres через read-only пользователя (из миграции
   этапа 2), Redis — только чтение счётчиков. Конфиг через pydantic-settings.
2. Секции сверху вниз:
   - Заголовок, 1-2 предложения о проекте, ссылка на GitHub, бейдж «данные обновляются live».
   - Live-блок: правок за последнюю минуту (сумма live-счётчиков из Redis), автообновление
     каждые ~10 сек (st_autorefresh или fragment), спарклайн за последние 60 минут.
   - График активности по часам за 7 дней (agg_edits_hourly): stacked по топ-10 вики + other.
   - Доля ботов/анонимов/зарегистрированных по дням (mart_editor_activity_daily).
   - Топ-20 страниц за сегодня (mart_top_pages_daily) таблицей с кликабельными ссылками
     на статьи Википедии.
3. Все SQL-запросы — в отдельном модуле, кэширование st.cache_data с TTL 60 сек
   (live-блок не кэшируется). Если витрины пустые — дружелюбная заглушка, не traceback.
4. Аккуратный лаконичный вид: wide layout, тёмная тема по умолчанию, без нагромождения.
5. Dockerfile, сервис в compose (порт 8501), healthcheck-эндпоинт Streamlit (/_stcore/health).
6. Тесты: модуль запросов (мок-подключение), форматирование данных для графиков.

Проверка: подними весь стек, дай поработать 10+ минут, покажи скриншот дашборда с живыми
данными. В конце: тесты и линтер зелёные, чекбоксы Этапа 5 в PLAN.md отмечены, PR-описание.
```

---

## Этап 6 — healthchecker

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-6-healthchecker.

Задача — Этап 6: сервис healthchecker (services/healthchecker) — мониторинг всего пайплайна
с алертами в Telegram.

Требования:
1. Цикл проверок раз в 60 сек, каждая проверка — отдельный класс с общим интерфейсом
   (name, check() -> CheckResult(status, details)):
   - KafkaLagCheck: суммарный lag группы pg-writer по wiki.recentchange (AdminClient);
     warn > 10k, critical > 50k или группа отсутствует.
   - FreshnessCheck: now() - max(event_ts) из raw.recentchange; warn > 5 мин, critical > 15 мин.
   - RedisCheck: PING + наличие live-счётчиков за последние 5 минут.
   - DbSizeCheck: размер БД (pg_database_size); warn выше порога из env.
   - DashboardCheck: GET на /_stcore/health дашборда.
2. Алерты в Telegram: переход OK → PROBLEM и PROBLEM → OK (recovery-сообщение).
   Троттлинг: повторный алерт по той же проверке не чаще раза в 30 мин. Состояние проверок —
   в Redis (переживает рестарт).
3. HTTP-эндпоинт /health (агрегированный статус всех проверок JSON-ом) — его будет
   опрашивать Railway healthcheck. Лёгкий сервер (например, uvicorn + FastAPI или aiohttp).
4. Конфиг pydantic-settings (все пороги через env), структурные логи, Dockerfile, в compose.
5. Тесты: каждая проверка с моками, логика переходов состояний и троттлинга (fakeredis),
   формат /health.

Проверка: подними стек, покажи /health со всеми OK; останови consumer — покажи алерт
(или лог алерта, если Telegram не настроен) в течение 2 минут; запусти обратно — recovery.
В конце: тесты и линтер зелёные, чекбоксы Этапа 6 в PLAN.md отмечены, PR-описание.
```

---

## Этап 7 — CI/CD и деплой на Railway

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Строго следуй зафиксированным в нём решениям.
Работай в ветке stage-7-deploy.

Задача — Этап 7: полный CI/CD и автономный прод на Railway. Я буду выполнять действия
в веб-интерфейсе Railway по твоим инструкциям — давай их пошагово и жди моего подтверждения.

Требования:
1. ci.yml (PR + push в main): lint (ruff) → tests (pytest всех сервисов) →
   dbt-check: поднять Postgres service-container, применить миграции, засеять фикстуры
   (небольшой сэмпл событий), dbt build. Все шаги обязаны быть зелёными для merge.
2. build-deploy.yml (push в main): матрица сборки образов producer/consumer/healthchecker/
   dashboard/airflow → GHCR (тег sha + latest), затем деплой на Railway через railway CLI
   (RAILWAY_TOKEN в GitHub Secrets) или redeploy-хук — выбери способ и обоснуй.
3. Схема сервисов на Railway (составь для меня пошаговую инструкцию):
   - managed Postgres и Redis (плагины Railway);
   - Kafka: один брокер KRaft из Docker-образа, внутренний listener для сервисов
     (private networking), volume для данных;
   - producer, consumer, healthchecker, dashboard, airflow — из GHCR-образов;
   - все переменные окружения по .env.example, healthcheck для dashboard и healthchecker;
   - миграции: job/entrypoint перед стартом consumer.
4. Проверь ресурсы: подбери стартовые лимиты RAM на сервис (Kafka и Airflow — самые тяжёлые),
   дай мне оценку месячной стоимости на Hobby-плане.
5. dbt docs: job в CI после merge в main — dbt docs generate на CI-базе → публикация
   на GitHub Pages (actions/deploy-pages).
6. docs/architecture.md: раздел «Deployment» — схема прод-окружения, как катится релиз,
   что где хранится, известные trade-offs (эфемерность Kafka-диска, один брокер и т.д.).

Проверка: push в main → CI зелёный → образы в GHCR → Railway обновился; дашборд доступен
по публичному URL, данные текут, Airflow крутит DAG-и, healthchecker шлёт /health OK.
В конце: чекбоксы Этапа 7 в PLAN.md отмечены, итоговая инструкция «что проверить руками».
```

---

## Этап 8 — полировка витрины проекта

```text
Ты работаешь над проектом Wiki Stream Analytics — пет-проект для портфолио Data Engineer.
Сначала прочитай PLAN.md в корне проекта целиком. Работай в ветке stage-8-polish.

Задача — Этап 8: превратить репозиторий в витрину для рекрутёров и техлидов.

Требования:
1. README.md (на английском — его будут читать иностранные рекрутёры):
   - шапка: название, одно предложение сути, бейджи (CI, лицензия), ссылки: live dashboard,
     dbt docs, LinkedIn;
   - секция Architecture: mermaid-диаграмма из PLAN.md (актуализируй под финальную реальность);
   - Tech stack списком с одним предложением «зачем» на каждую технологию;
   - Key engineering decisions: 4-5 пунктов (delivery guarantees, партиционирование+retention,
     идемпотентность, инкрементальные dbt-модели, мониторинг) — коротко, со ссылкой на
     docs/architecture.md;
   - Quickstart: docker compose up + что где открыть (5 минут до работающего стека);
   - скриншот или GIF дашборда.
2. docs/architecture.md — финализировать: все ключевые решения и trade-offs в ADR-стиле
   (контекст → решение → последствия). Это ответы на вопросы с собеседований.
3. Пройдись по всем docstring и логам сервисов — единый стиль, английский язык.
4. Проверь, что PLAN.md полностью отмечен, добавь в конец секцию "Что дальше" (сателлит:
   LLM Data Quality Monitor).
5. Подготовь мне 3-4 предложения для резюме и LinkedIn: как описать проект одной строкой
   в CV и коротким постом в LinkedIn (на английском).

В конце: линтер зелёный, PR-описание, список из 5 вопросов, которые мне могут задать
про этот проект на собеседовании, с короткими ответами.
```
