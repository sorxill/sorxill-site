# Что построено на самом деле

Документ существует, потому что HLD и LLD описывают **целевую** систему,
а этот файл — **фактическую**. Обновляется в конце каждого milestone.

**Дата:** 2026-07-31 · **Прод:** https://sorxill.ru работает

## Готово

| Компонент | Состояние |
|---|---|
| Слои бэкенда | `domain` / `application` / `infrastructure` / `api`, границы проверяет `lint-imports` |
| Домен | `Project`, `Slug`, `Locale`, `PublishStatus`, инвариант публикации |
| Use cases | `ListPublishedProjects`, `PublishProject` |
| Порты | `ProjectRepository`, `Clock`, `TaskQueue` |
| Реализации портов | in-memory (тесты) + SQLAlchemy (прод), обе проходят контрактные тесты |
| БД | PostgreSQL 17, Alembic, миграция `0001`: projects, project_translations, users, contact_messages, feed_items, audit_log |
| API | `GET /health`, `GET /readyz` (реально проверяет БД), `GET /api/v1/projects` |
| Фронтенд | Next.js 16, i18n ru/en, SSG обеих локалей, деградация при недоступном API |
| Инфраструктура | Traefik v3.6 + TLS от Let's Encrypt, Postgres, Redis |
| CI | ruff, ruff format, mypy strict, lint-imports, цикл миграций, pytest (порог 85%), tsc, eslint, vitest, next build, size-limit, gitleaks |
| CD | образы в GHCR, Trivy → Security, `.env.secrets` из Environment, миграции one-shot, rollout с health-gate и автооткатом, smoke снаружи |
| Тесты | 40 бэкенд (покрытие 92%), 3 фронтенд |

## Не сделано, хотя описано в LLD

| Что | Milestone | Примечание |
|---|---|---|
| Дизайн из макета | M2 | Сейчас страница — голая разметка без стилей |
| Мобильная вёрстка | M2 | Правило mobile-first есть, применять не к чему |
| `app/api/middleware.py` | M3 | `request_id`, тайминги — сейчас нет сквозного `trace_id` |
| `app/workers/` (ARQ) | M3 | Очередь задач; `TaskQueue` пока `RecordingTaskQueue` в памяти |
| Форма обратной связи, `contact_messages` | M3 | Таблица создана, кода нет |
| Резюме, бронирование | M3 | |
| Админка, RBAC, TOTP, `audit_log` | M4 | Таблицы `users`, `audit_log` созданы, кода нет |
| Лента GitHub, `feed_items` | M4 | Таблица создана, адаптеров нет |
| Umami, Grafana Alloy | M5 | Описаны в `docker-compose.prod.yml`, на сервере **не запущены** |
| Бэкапы на проде | M5 | `backup.sh` написан, cron не настроен, restore не проверялся |
| Сервер B (мониторинг, offsite) | M5 | Не подключён |
| Playwright e2e | M2 | В LLD описаны 5 сценариев, ни одного не написано |

## Долги и известные проблемы

1. **`ufw` и `fail2ban` на сервере отключены.** Пришлось выключить при
   восстановлении доступа. Включать по одному с проверкой SSH после каждого шага.
   В логах видно активное сканирование ботами — это не теория.
2. **Часть несуществующих путей отдаёт 500 вместо 404.** Видно в логах Traefik
   на запросах вида `/wp-config.php`. Ошибка в обработке, не в маршрутизации.
3. **Текст «API недоступен» показывается и при пустом списке проектов.**
   Одно условие на два разных случая: ошибка запроса и пустой ответ.
4. **База пуста.** Наполнение появится с админкой в M4; до этого список проектов пустой.
5. **`eslint` и `typescript` заморожены на мажорах** (9 и 5) — новые версии ломают
   `eslint-config-next`. Запрет и условие снятия — в `.github/dependabot.yml`.
6. **Сборка образа не покрыта проверками.** Проверяется установка колеса, но не
   слои Dockerfile — Docker в среде разработки недоступен.
