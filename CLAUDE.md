# CLAUDE.md

Инструкции для Claude Code при работе в этом репозитории.

## Что это

`sorxill.ru` — персональный сайт-визитка Python backend инженера.
Next.js 16 (web) + FastAPI (api), Docker Compose на выделенном VPS в Нидерландах.
Проект личный: ревьюера нет, гейтом служит CI.

Полная архитектура — `docs/01-HLD.md`, детали — `docs/02-LLD.md`,
все решения с альтернативами и минусами — `docs/adr/`.

## Состояние: M1 завершён, сайт в проде

Работает: `https://sorxill.ru` под валидным TLS, Postgres с миграциями,
пайплайн `коммит → checks → тег → release → прод` с автооткатом.

Не сделано: дизайн (M2), формы и резюме (M3), админка и лента (M4),
observability и бэкапы на проде (M5). Подробности — раздел «Дальше» ниже.

## Архитектурные правила

Нарушение 1–6 ломает CI. 7–9 — на совести автора.

1. `web` никогда не ходит в Postgres напрямую. Единственный путь к данным — через `api`.
2. `app/domain/` не импортирует FastAPI, SQLAlchemy, Pydantic. Проверяет `lint-imports`.
3. Инварианты живут в сущностях (`Project.publish()`), а не в роутерах.
4. Новая реализация порта обязана пройти `tests/contract/` для этого порта.
5. Образы не собираются на сервере — только в CI. На 2 ядрах сборка положит сайт.
6. Каждый контейнер имеет явный лимит памяти.
7. Миграции обратно совместимы: expand → migrate → contract.
8. Компоненты авторятся mobile-first.
9. Неочевидное решение → ADR в `docs/adr/` по шаблону `0000-template.md`.

## Команды

```bash
make dev            # локальное окружение: web :3000, api :8000/docs
make test           # pytest + vitest
make lint           # ровно то, что проверит CI
```

Бэкенд отдельно (из `apps/api`, нужен `DATABASE_URL`):
```bash
ruff check . && ruff format --check . && mypy app && lint-imports && pytest
alembic upgrade head && alembic downgrade base && alembic upgrade head
```

Фронтенд отдельно (из `apps/web`):
```bash
npm run typecheck && npm run lint && npm run test && npm run build && npx size-limit
```

## Проверка перед коммитом — обязательна

Этот проект уже потерял много времени на «у меня работает». Правила:

- **Изменил `pyproject.toml` — проверь установку в чистом venv**, а не в текущем
  окружении: `python -m venv /tmp/v && /tmp/v/bin/pip install -e ".[dev]"`.
  Пакет мог остаться от прежней ручной установки, и mypy найдёт то, чего в CI нет.
- **Изменил Dockerfile — собери колесо и проверь импорт вне каталога исходников.**
  Editable-установка скрывает ошибки упаковки.
- **Alpine — это busybox.** `wget` там не понимает `--spider`, `--max-redirect`
  и прочие опции GNU. Health-check пишется в простейшей форме.
- **Изменил `package.json` — пересобери `package-lock.json` в том же коммите.**
  Иначе `npm ci` в CI падает с EUSAGE.
- Не выполняй `npm audit fix --force`: он предлагал «починить» проект откатом
  Next с 16 на 9. Разбор аудита — `docs/runbooks/dependencies.md`.

## Деплой

Два независимых workflow (ADR-0018):

| | триггер | что делает | время |
|---|---|---|---|
| `checks.yml` | push, PR | линт, типы, границы слоёв, тесты, сборка, size-limit, gitleaks | 2–3 мин |
| `release.yml` | тег `v*`, вручную | образы → GHCR, Trivy, `.env.secrets` на сервер, миграции, rollout, smoke | 7–10 мин |

Релиз: смержить PR от release-please → создастся тег → деплой.
Откат: `gh workflow run release.yml -f rollback_sha=<sha>`.

Секреты — в GitHub Environment `production` (ADR-0016). `.env` на сервере
собирает `rollout.sh` из `.env.secrets`; руками его не редактируют.

## Грабли, на которые уже наступали

Все проверены на этом сервере, не теоретические:

| Симптом | Причина |
|---|---|
| Compose подставляет пустые переменные, `ghcr.io//image` | `.env` ищется в каталоге первого `-f` файла. Нужен явный `--env-file` |
| Traefik: `client version 1.24 is too old` | Docker 28+ не отвечает по старому API. Нужен `DOCKER_API_VERSION=1.44` |
| `/api/...` уходит в Next вместо FastAPI | Имя роутера `api` зарезервировано под `api@internal`. Наш называется `backend` |
| Метки Traefik не применились после деплоя | Compose не пересоздаёт контейнер, если совпал config-hash. Нужен `--force-recreate` |
| `/` отдаёт 404 вместо редиректа на `/ru` | При наличии `src/` файл `proxy.ts` обязан лежать в `src/`, а не в корне |
| Next слушает `http://<id контейнера>:3000` | Docker выставляет `HOSTNAME`. Нужен явный `ENV HOSTNAME=0.0.0.0` |
| `SettingsError` на `cors_origins` | pydantic-settings парсит списки как JSON до валидатора. Нужен `NoDecode` |
| Потерян SSH-доступ после bootstrap | Ключ ставится ДО ужесточения SSH (ADR-0020) |

## Стиль

- Комментарии и документация — по-русски, код и идентификаторы — по-английски.
- Комментарий объясняет **почему**, а не что. Если «почему» тянет на решение — это ADR.
- Коммиты — conventional commits, скоупы: `api`, `web`, `domain`, `infra`, `ci`, `docs`, `design`, `deps`.
  Готовые команды: `/commit` и `/adr` в `.claude/commands/`.
- Порог покрытия 85% не понижается. Только вверх.

## Дальше по плану

- **M2** — перенос макета в компоненты, mobile-first. Макет: `docs/03-homepage-mockup.html`
  (рабочий, с анимациями), токены: `apps/web/src/styles/tokens.css`.
- **M3** — форма обратной связи, резюме, бронирование звонка.
- **M4** — админка, RBAC, TOTP, лента GitHub, audit log.
- **M5** — observability, бэкапы с проверенным restore, hardening.

**Долг, который нельзя забыть:** на сервере отключены `ufw` и `fail2ban` — их
пришлось выключить при восстановлении доступа. Включать по одному, с проверкой
SSH после каждого шага.
