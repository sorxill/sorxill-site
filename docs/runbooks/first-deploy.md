# Runbook: от git init до работающего сайта

Вы уже сделали `git init`. Дальше по порядку. Каждый шаг проверяемый —
не переходите к следующему, пока текущий не дал ожидаемый результат.

## Шаг 1. Проверить, что секреты не уедут в историю

```bash
grep -x '\.env' .gitignore && echo "ok"
ls -a | grep -x '\.env' && echo "ВНИМАНИЕ: .env существует, проверьте что он в .gitignore" || echo "ok: .env нет"
```

Секрет, попавший в git-историю, считается скомпрометированным навсегда — он остаётся
в кэше GitHub и во всех клонах. Лечится только ротацией, а не удалением коммита.

## Шаг 2. Первый коммит

```bash
git add .
git status              # посмотрите глазами: .env быть не должно
git commit -m "feat: walking skeleton — слои api, тесты, пайплайн, инфраструктура"
```

## Шаг 3. Репозиторий на GitHub

```bash
gh auth login
gh repo create sorxill.ru --public --source=. --push \
  --description "Персональный сайт-визитка: Next.js 16, FastAPI, Docker, VPS"

gh repo edit --homepage "https://sorxill.ru" \
  --add-topic fastapi --add-topic nextjs --add-topic python \
  --add-topic typescript --add-topic docker --add-topic clean-architecture
```

**Ожидаемо:** пайплайн запустится и упадёт на джобе `web` — `package-lock.json`
ещё не существует, а `npm ci` без него не работает. Это нормально, чиним в шаге 4.

## Шаг 4. Зафиксировать зависимости фронтенда

```bash
cd apps/web && npm install && cd ../..
git add apps/web/package-lock.json
git commit -m "build(web): зафиксировать package-lock"
git push
```

`npm install` может поругаться на версии — правьте `package.json` до зелёного.
Это единственная часть каркаса, которую я не смог проверить у себя.

**Ожидаемо:** пайплайн зелёный, в Packages появились два образа.

## Шаг 5. Сделать образы доступными серверу

Packages → `sorxill-api` → Package settings → Change visibility → Public.
То же для `sorxill-web`. Иначе серверу понадобится токен на каждый pull.

## Шаг 6. Подготовить сервер A

```bash
scp infra/scripts/bootstrap-vps.sh root@<ip-сервера-A>:/tmp/
ssh root@<ip-сервера-A> bash /tmp/bootstrap-vps.sh
```

Скрипт делает: swap 2 ГБ, Docker с ротацией логов, пользователь `deploy`,
UFW на 22/80/443, fail2ban, запрет root-логина и парольной аутентификации.

Ключ для деплоя — отдельный от вашего личного:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sorxill_deploy -C "github-actions" -N ""
ssh-copy-id -i ~/.ssh/sorxill_deploy.pub deploy@<ip-сервера-A>
```

**Проверка:** `ssh -i ~/.ssh/sorxill_deploy deploy@<ip> docker ps` работает,
`ssh root@<ip>` больше нет.

## Шаг 7. DNS

В личном кабинете reg.ru: A-записи `@` и `www` → IP сервера A, TTL 300.
Позже добавите `analytics` для Umami.

**Проверка:** `dig +short sorxill.ru` возвращает ваш IP. Может занять до часа.
До этого Let's Encrypt сертификат не выдаст — HTTP-01 challenge требует
работающего DNS.

## Шаг 8. Создать окружение production и залить секреты

Settings → Environments → New environment → `production`.
Опционально включите там же **Required reviewers** — тогда деплой будет ждать вашего
подтверждения кнопкой. Для одиночки скорее лишнее, но если боитесь случайного пуша в
пятницу вечером, это ровно та защита.

Дальше один скрипт вместо ручного редактирования:

```bash
./infra/scripts/init-secrets.sh
```

Он сгенерирует случайные `SECRET_KEY`, `IP_PEPPER`, `REVALIDATE_SECRET`,
`UMAMI_SECRET`, `POSTGRES_PASSWORD` и спросит те, что сгенерировать нельзя
(SMTP, токен GitHub, Sentry). Пустой ввод — пропустить, зальёте позже.

**Проверка:** `gh secret list --env production` показывает список.

⚠️ `.env` на сервере создавать руками не нужно — пайплайн соберёт его сам из этих
секретов при каждом деплое и положит с правами `600`. Если отредактируете файл
вручную, следующий деплой всё перезапишет.

⚠️ `POSTGRES_PASSWORD` меняется свободно только **до** первого деплоя. После — пароль
уже внутри базы, и ротация требует `ALTER USER sorxill WITH PASSWORD '...'` в том же
окне, иначе приложение потеряет доступ.

## Шаг 9. Секреты и переменные уровня репозитория

```bash
gh secret set DEPLOY_KEY    < ~/.ssh/sorxill_deploy
gh secret set SERVER_A_HOST --body "<ip сервера A>"
gh secret set TG_TOKEN      --body "<токен бота>"
gh secret set TG_CHAT       --body "<chat id>"
gh variable set DOMAIN      --body "sorxill.ru"
gh variable set ACME_EMAIL  --body "<ваш email для Let's Encrypt>"
```

Разница между secret и variable простая: variable видно в логах, secret маскируется.
Домен — не секрет, пароль — секрет.

Бот для уведомлений: @BotFather → `/newbot`, свой chat id — у @userinfobot.
Уведомления приходят только при падении деплоя: успешные не нужны, к ним привыкаешь
и перестаёшь замечать.

## Шаг 9.5. Включить защиту от утечек на стороне GitHub

Settings → Code security:

- **Secret scanning** — включить
- **Push protection** — включить

Это важнее, чем `gitleaks` в пайплайне: gitleaks ловит секрет уже **после** коммита,
а push protection блокирует сам `git push`. Для публичного репозитория обе функции
бесплатны.

## Шаг 10. Деплой

```bash
git commit --allow-empty -m "ci: первый деплой"
git push
```

**Ожидаемо:** через 3-5 минут `https://sorxill.ru/ru` отдаёт страницу по HTTPS,
`https://sorxill.ru/api/v1/projects` — JSON с одним проектом.

Если упало — смотрите лог джобы `deploy`. `rollout.sh` при неудачном health-check
сам вернёт предыдущий образ, так что сайт не останется в сломанном состоянии.

## Откат вручную

```bash
gh workflow run pipeline.yml -f rollback_sha=<предыдущий sha>
# или прямо на сервере:
ssh deploy@<ip> "cd /opt/sorxill && ./infra/scripts/rollout.sh --rollback"
```

## Дальше

M1: Postgres и Alembic вместо in-memory репозитория. Миграции применяются
в `rollout.sh` до старта нового кода, поэтому схема обязана быть обратно
совместимой: expand → migrate → contract.
