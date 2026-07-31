#!/usr/bin/env bash
# Разовая генерация секретов и заливка в GitHub Environment production.
# После этого .env на сервере создаётся пайплайном автоматически,
# руками его редактировать не нужно никогда.
set -euo pipefail

ENV_NAME=production
gh auth status >/dev/null || { echo "Сначала: gh auth login"; exit 1; }

put() { printf '%s' "$2" | gh secret set "$1" --env "$ENV_NAME"; echo "  ✓ $1"; }

echo "Генерирую случайные секреты…"
put SECRET_KEY        "$(openssl rand -hex 32)"
put IP_PEPPER         "$(openssl rand -hex 32)"
put REVALIDATE_SECRET "$(openssl rand -hex 32)"
put UMAMI_SECRET      "$(openssl rand -hex 32)"
put POSTGRES_PASSWORD "$(openssl rand -hex 24)"

echo
echo "Теперь то, что нельзя сгенерировать. Enter — пропустить, зальёте позже."
for name in SMTP_HOST SMTP_USER SMTP_PASSWORD GH_TOKEN_READONLY SENTRY_DSN GRAFANA_CLOUD_TOKEN; do
  read -rsp "$name: " value; echo
  [[ -n "$value" ]] && put "$name" "$value" || echo "  — пропущен"
done

echo
echo "Готово. Проверить: gh secret list --env $ENV_NAME"
echo "Ротация любого: gh secret set <ИМЯ> --env $ENV_NAME  и повторный запуск пайплайна."
echo "⚠️  POSTGRES_PASSWORD после первого деплоя меняется только вместе с ALTER USER в базе."
