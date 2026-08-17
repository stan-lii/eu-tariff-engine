.PHONY: lint type test licence check up down up-obs up-parse dev migrate seed eval health

lint:
	uv run ruff format --check src/ tests/
	uv run ruff check src/ tests/

type:
	uv run mypy src/
	uv run lint-imports

test:
	uv run pytest tests/ -m "unit or contract" --tb=short -q || test $$? -eq 5

licence:
	./scripts/check_licences.sh

check: lint type test licence

up:
	docker compose --profile core up -d
	@echo "Core services started. Run 'make health' to verify."

down:
	docker compose -p tariff-engine down

up-obs:
	docker compose --profile core --profile obs up -d
	@echo "Core + Observability started. Langfuse at http://localhost:3000"

up-parse:
	docker compose --profile core --profile parse up -d
	@echo "Core + Parse started."

dev: up
	uv run dagster dev -m tariff_engine.interfaces.definitions

migrate:
	@echo "Migrations not yet configured. Added in Phase 2."

seed:
	@echo "Seed data not yet configured. Added in Phase 3."

eval:
	@echo "Evaluation suite not yet configured. Added in Phase 6."

health:
	@bash scripts/health-check.sh
