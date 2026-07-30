#!/usr/bin/env bash
# Восстанавливает свежайший дамп в одноразовый контейнер и проверяет, что данные на месте.
# Бэкап, восстановление которого никто не проверял, бэкапом не является.
set -euo pipefail
cd "$(dirname "$0")/../.."
source .env.secrets

LATEST="$(ls -t /tmp/sorxill-*.sql.gz.age 2>/dev/null | head -1 || true)"
[[ -n "$LATEST" ]] || { echo "FAIL: свежего дампа нет"; exit 1; }

NAME="verify-$RANDOM"
docker run -d --rm --name "$NAME" \
  -e POSTGRES_PASSWORD=verify -e POSTGRES_DB=verify \
  --memory 512m postgres:17-alpine >/dev/null
trap 'docker rm -f "$NAME" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 30); do
  docker exec "$NAME" pg_isready -U postgres -q && break
  sleep 1
done

age -d -i ~/.age/key.txt "$LATEST" | gunzip \
  | docker exec -i "$NAME" psql -U postgres -d verify -q >/dev/null

TABLES="$(docker exec "$NAME" psql -U postgres -d verify -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"

[[ "$TABLES" -ge 1 ]] || { echo "FAIL: восстановлено 0 таблиц"; exit 1; }
echo "OK: восстановлено таблиц: $TABLES, файл $(basename "$LATEST")"
