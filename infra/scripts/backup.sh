#!/usr/bin/env bash
# Ночной бэкап с шифрованием и выгрузкой в S3 + на сервер B.
set -euo pipefail
cd "$(dirname "$0")/../.."
source .env.secrets

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="/tmp/sorxill-$STAMP.sql.gz.age"

docker compose -f infra/compose/docker-compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" --clean --if-exists "$POSTGRES_DB" \
  | gzip -9 | age -r "$AGE_RECIPIENT" > "$FILE"

aws s3 cp "$FILE" "s3://$S3_BUCKET/db/" --endpoint-url "$S3_ENDPOINT" --only-show-errors
scp -q "$FILE" "deploy@$SERVER_B_HOST:/opt/backups/" || echo "WARN: сервер B недоступен"
rm -f "$FILE"
echo "✓ backup $STAMP"
