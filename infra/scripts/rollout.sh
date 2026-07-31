#!/usr/bin/env bash
# Zero-downtime подмена web и api с health-gate и автооткатом.
#   ./rollout.sh <sha>      обычный деплой
#   ./rollout.sh --rollback вернуть предыдущий образ
#
# Разделение ответственности:
#   .env.secrets     — пишет пайплайн из GitHub Environment. Руками не правим.
#   .deploy-current  — текущий тег, владеет этот скрипт.
#   .deploy-previous — предыдущий тег для откката.
#   .env             — генерируется здесь как .env.secrets + теги. В git не попадает.
set -euo pipefail

cd "$(dirname "$0")/../.."
# --env-file обязателен: compose ищет .env в каталоге первого -f файла
# (infra/compose/), а не в текущем. Без него все переменные пустые
# и образ превращается в "ghcr.io//sorxill-api".
# --project-directory не трогаем: относительные пути томов в compose-файлах
# считаются от него, и их сдвиг сломает монтирование конфигов.
COMPOSE="docker compose --env-file /opt/sorxill/.env \
  -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.prod.yml"

[[ -f .env.secrets ]] || { echo "Нет .env.secrets — пайплайн ещё не приносил секреты"; exit 1; }

if [[ "${1:-}" == "--rollback" ]]; then
  [[ -f .deploy-previous ]] || {
    echo "Откатываться некуда: это первый деплой, предыдущей версии не существует."
    echo "Смотрите логи: docker logs --tail 50 sorxill-web-1"
    exit 1
  }
  TAG="$(cat .deploy-previous)"
  echo "Откат на $TAG"
else
  TAG="${1:?Укажите SHA образа}"
  [[ -f .deploy-current ]] && cp .deploy-current .deploy-previous
fi

render_env() {
  umask 077
  { cat .env.secrets; printf 'API_TAG=%s\nWEB_TAG=%s\n' "$1" "$1"; } > .env
}
render_env "$TAG"

# Ранняя внятная ошибка вместо "invalid reference format" на середине деплоя.
for var in DOMAIN GH_OWNER ACME_EMAIL POSTGRES_PASSWORD API_TAG WEB_TAG; do
  value="$(grep -m1 "^${var}=" .env | cut -d= -f2-)"
  [[ -n "$value" ]] || { echo "В .env пусто: $var — проверьте секреты окружения production"; exit 1; }
done

$COMPOSE pull api web

# Инфраструктурные сервисы поднимаем явно: подмена приложения идёт
# с --no-deps, поэтому Traefik, Postgres и Redis сами по себе не стартуют.
# Без Traefik порт 80 никто не слушает и smoke-тест падает при живых
# и здоровых контейнерах приложения.
$COMPOSE up -d --wait --wait-timeout 90 postgres redis
$COMPOSE up -d traefik

# Миграции one-shot до старта нового кода. Схема обратно совместима
# (expand → migrate → contract), поэтому старая версия продолжает работать.
$COMPOSE run --rm api alembic upgrade head || { echo "Миграции упали, деплой отменён"; exit 1; }

for svc in api web; do
  echo "→ подменяю $svc"
  if ! $COMPOSE up -d --no-deps --wait --wait-timeout 150 "$svc"; then
    echo "$svc не стал healthy, откатываюсь"
    [[ "${1:-}" != "--rollback" ]] && exec bash "$0" --rollback
    exit 1
  fi
done

DOMAIN_VALUE="$(grep -m1 '^DOMAIN=' .env.secrets | cut -d= -f2)"
if ! curl -fsS --max-time 5 http://127.0.0.1/api/v1/projects -H "Host: $DOMAIN_VALUE" >/dev/null; then
  echo "smoke провален. Состояние контейнеров:"
  $COMPOSE ps
  echo "Последние строки Traefik:"
  $COMPOSE logs --tail 20 traefik || true
  echo "откатываюсь"
  [[ "${1:-}" != "--rollback" ]] && exec bash "$0" --rollback
  exit 1
fi

# Сертификат выдаётся асинхронно после первого обращения к домену.
# Разогреваем и показываем результат, чтобы проблема ACME была видна
# здесь, а не через шаг во внешнем smoke-тесте.
curl -s --max-time 15 -o /dev/null "https://$DOMAIN_VALUE/" --insecure || true
sleep 8
if ! curl -fsS --max-time 10 -o /dev/null "https://$DOMAIN_VALUE/"; then
  echo "⚠️  Сертификат ещё не выдан. Логи ACME:"
  $COMPOSE logs --tail 30 traefik 2>&1 | grep -iE "acme|certificate|error" || true
fi

echo "$TAG" > .deploy-current
docker image prune -af --filter "until=72h" >/dev/null 2>&1 || true
echo "✓ deployed $TAG"
