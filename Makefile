COMPOSE_LOCAL = docker compose -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.local.yml

.PHONY: help dev down logs test lint fmt api-shell psql deploy rollback backup
help:  ## список команд
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/ —/' | sort

dev:  ## поднять локальное окружение
	$(COMPOSE_LOCAL) up -d --build
	@echo "web  → http://localhost:3000/ru"
	@echo "api  → http://localhost:8000/docs"

down:  ## остановить локальное окружение
	$(COMPOSE_LOCAL) down

logs:  ## логи всех сервисов
	$(COMPOSE_LOCAL) logs -f --tail=100

test:  ## тесты бэкенда и фронтенда
	cd apps/api && pytest
	cd apps/web && npm run test

lint:  ## всё, что проверяет CI, локально
	cd apps/api && ruff check . && ruff format --check . && mypy app && lint-imports
	cd apps/web && npm run typecheck && npm run lint

fmt:  ## автоформатирование
	cd apps/api && ruff format . && ruff check --fix .

psql:  ## консоль базы
	$(COMPOSE_LOCAL) exec postgres psql -U sorxill -d sorxill

deploy:  ## деплой текущего main (обычно делает CI)
	gh workflow run cd.yml

rollback:  ## откат на предыдущий образ
	ssh deploy@$$SERVER_A_HOST "cd /opt/sorxill && ./infra/scripts/rollout.sh --rollback"

backup:  ## бэкап прода вручную
	ssh deploy@$$SERVER_A_HOST "cd /opt/sorxill && ./infra/scripts/backup.sh"
