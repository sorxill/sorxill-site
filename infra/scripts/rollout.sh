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
  [[ -f .deploy-previous ]] || { echo "Нет сохранённого предыдущего тега"; exit 1; }
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
for var in DOMAIN GH_OWNER POSTGRES_PASSWORD API_TAG WEB_TAG; do
  value="$(grep -m1 "^${var}=" .env | cut -d= -f2-)"
  [[ -n "$value" ]] || { echo "В .env пусто: $var — проверьте секреты окружения production"; exit 1; }
done

$COMPOSE pull api web

# Миграции one-shot до старта нового кода. Схема обратно совместима
# (expand → migrate → contract), поэтому старая версия продолжает работать.
$COMPOSE run --rm api alembic upgrade head || { echo "Миграции упали, деплой отменён"; exit 1; }

for svc in api web; do
  echo "→ подменяю $svc"
  if ! $COMPOSE up -d --no-deps --wait --wait-timeout 90 "$svc"; then
    echo "$svc не стал healthy, откатываюсь"
    [[ "${1:-}" != "--rollback" ]] && exec bash "$0" --rollback
    exit 1
  fi
done

DOMAIN_VALUE="$(grep -m1 '^DOMAIN=' .env.secrets | cut -d= -f2)"
if ! curl -fsS --max-time 5 http://127.0.0.1/api/v1/projects -H "Host: $DOMAIN_VALUE" >/dev/null; then
  echo "smoke провален, откатываюсь"
  [[ "${1:-}" != "--rollback" ]] && exec bash "$0" --rollback
  exit 1
fi

echo "$TAG" > .deploy-current
docker image prune -af --filter "until=72h" >/dev/null 2>&1 || true
echo "✓ deployed $TAG"
