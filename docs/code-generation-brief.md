# Code Generation Brief

Paste this at the start of every chat session where you request code for the EU Tariff Engine.

---

## Project

- Package: `tariff_engine` (in `src/tariff_engine/`).
- Distribution: `eu-tariff-engine`.
- Python 3.13. `uv` only. No `pip install`.
- Licence: Apache-2.0. No AGPL, GPL or SSPL in the runtime dependency tree.
## Layering (enforced by import linter)

```
domain  <-  application  <-  adapters  <-  interfaces
```

- `domain`: Pydantic models, value objects, temporal logic, validation rules. Zero I/O.
- `application`: use cases, orchestration via abstract ports only.
- `adapters`: source clients, database repositories, LLM providers, parsers, object storage.
- `interfaces`: FastAPI routes, CLI, MCP server, Dagster assets.
- Inner layers never import outer layers.
## Naming

- Packages/modules: `snake_case`, singular.
- Classes: `PascalCase`. Source models suffixed (`TaricMeasureRecord`), domain models unsuffixed (`Measure`).
- Adapters: `<Source>Client` (transport), `<Source>Adapter` (port implementation).
- DB tables: `snake_case` plural. Temporal columns: `valid_from`, `valid_to`, `recorded_at`, `superseded_at`.
- Dagster assets: `<source>_<verb>_<object>`.
- Tests: `src/pkg/a/b.py` maps to `tests/unit/pkg/a/test_b.py`.
## Data Contracts

- Every external payload parsed into a Pydantic v2 model at the adapter boundary. No raw dicts inward.
- Models: `frozen=True`, `extra="forbid"` by default.
- Money, rates, quantities: `Decimal`, never `float`. Currency always explicit.
- Dates: `date` or timezone-aware `datetime` in UTC. No naive datetimes.
## Error Handling

- Hierarchy root: `TariffEngineError`.
- Branches: `SourceError`, `ValidationError`, `TemporalError`, `ExtractionError`, `ConfigurationError`, `BudgetError`.
- Adapters translate all third-party exceptions. No `httpx` exception escapes.
- Never swallow exceptions. Handle or re-raise with context.
- Retries only on transient `SourceError` subclasses via `tenacity` (exponential backoff, jitter, capped).
## Configuration

- `pydantic-settings`, one `Settings` object, loaded once, injected. No module-level env reads.
- Secrets never in logs, traces, prompts, or fixtures.
## LLM Rules

- No prompt inline in code. Prompts in `prompts/<name>/<version>.md`, loaded by identifier.
- Every LLM call: typed function, Pydantic input model, Pydantic output model.
- Model choice is configuration. Reference tiers (extraction, escalation, adjudication), not model names.
- Only `adapters/llm/` imports a vendor SDK.
- Every call declares workload profile: `pipeline` or `client_facing`.
- Every call carries a token budget, respects per-run and monthly accumulators. Breach raises `BudgetError`.
- LLM output is never a released value. It is a candidate requiring validation and reconciliation.
## Observability

- `structlog` JSON with `run_id`, `source`, `measure_id`.
- OTel spans on every adapter call, LLM call, pipeline asset.
- Every LLM call records: model, prompt version, tokens, cost, latency.
- Trace failure or quota exhaustion blocks the pipeline.
## Testing

- `pytest` markers: `unit`, `integration`, `contract`, `eval`, `live`.
- Default run: `unit` and `contract` only, offline, deterministic.
- Network blocked at socket level in unit tests.
- LLM calls replayed from cassettes. `live` tests on schedule only.
- Every adapter: contract test against frozen payload in `tests/fixtures/sources/<source>/`.
## Module Template

Every new package contains:

```
<module>/
  __init__.py     exports public surface only
  models.py       Pydantic contracts
  ports.py        Protocol classes
  service.py      use case logic, no I/O
  errors.py       module exceptions from shared hierarchy
  README.md       purpose, inputs, outputs, invariants
```

Adapters add: `client.py`, `mapper.py`, `fixtures/`.

## Adapter Contract

Every source adapter implements:

1. `discover()`: what is available, with content hash per item.
2. `fetch(ref)`: raw bytes plus metadata, persisted to object storage before parsing.
3. `parse(raw)`: raw to source-specific Pydantic records.
4. `map(records)`: source records to canonical domain models.
5. `provenance()`: source ID, legal basis, retrieval time, licence, reuse terms.
Provenance travels with models into `record_measure_version()`. It is never discarded.

## Forbidden Actions

- No new dependency without an ADR naming its licence.
- No copyleft dependency in the runtime tree.
- No schema change without an Alembic migration.
- No direct SQL outside repository classes.
- No prompt inline in code.
- No snippets or placeholders. Complete files only.
- No `float` for money or rates.
- No naive datetimes.
- No hard-coded model names. Use tier references.
- No vendor SDK import outside `adapters/llm/`.
- No swallowed exceptions.
- No untraced LLM calls.
## Output Format

- One complete file per response, including all imports and the module docstring.
- Provide the matching test file in the same response.
- Full type annotations on the first pass.
- If editing, the current file will be pasted first. Do not describe it; read it.
