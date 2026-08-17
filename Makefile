.PHONY: lint type test licence check

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
