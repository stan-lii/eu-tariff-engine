# Engineering Constitution

**Project:** EU Tariff Compliance and Validation Engine
**Status:** Binding from the first commit. Every commit is checked against this document.
**Updates:** Changes require an ADR and regeneration of `docs/code-generation-brief.md`.

---

## Language and Runtime

- Python 3.13 pinned via `.python-version`. Revisit at Phase 5 once the parser dependency tree is fixed. Never use the free-threaded build.
- `uv` for all dependency and environment management. `uv.lock` is committed. No `pip install` in any documented workflow.
- One monorepo, `src/` layout, single virtual environment.
- All development happens inside WSL2 Ubuntu. `.gitattributes` enforces LF.
## Layering Rule (enforced by import linter)

```
domain  <-  application  <-  adapters  <-  interfaces
```

- `domain`: Pydantic models, value objects, temporal logic, validation rules. Zero I/O, zero third-party clients, zero LLM calls. Must be importable with no network and no database.
- `application`: use cases, orchestration of domain plus ports. Depends on abstract ports only.
- `adapters`: source clients, database repositories, LLM providers, parsers, object storage.
- `interfaces`: FastAPI routes, CLI, MCP server, Dagster assets.
- An inner layer must never import an outer layer. Checked in CI, not by convention.
## Typing and Quality Gates

- `ruff` for lint and format, single config, line length 100.
- `mypy --strict` on `src/`. No `Any` in public signatures. No `# type: ignore` without an inline reason.
- `pre-commit` hooks: ruff, mypy, gitleaks, end of file, trailing whitespace, `uv lock --check`.
- Test coverage floor 85 percent on `domain` and `application`, 60 percent overall. Coverage is a floor, not a target.
## Licensing

- No AGPL, GPL or SSPL dependency in the runtime tree. CI fails on one.
- Any copyleft development-only tool is listed explicitly with its exemption reason.
- Every new dependency arrives with an ADR naming its licence.
## Data Contracts

- Every external payload is parsed into a Pydantic v2 model at the adapter boundary. Raw dicts never travel inward.
- Models are `frozen=True` and `extra="forbid"` by default. Loosen only with a comment explaining why.
- Every measure type has its own strict schema. Free-form JSON from an LLM is never accepted or persisted.
- All money, rates and quantities use `Decimal`, never `float`. Currency is always explicit.
- All dates are `date` or timezone-aware `datetime` in UTC. Naive datetimes are a lint failure.
## Naming

- Packages and modules: `snake_case`, singular (`measure`, not `measures`) except for collection modules.
- Classes: `PascalCase`. Pydantic models describing a source payload are suffixed with the source (`TaricMeasureRecord`), canonical domain models are unsuffixed (`Measure`).
- Adapters: `<Source>Client` for transport, `<Source>Adapter` for the port implementation.
- Database tables: `snake_case` plural. Bitemporal columns are always `valid_from`, `valid_to`, `recorded_at`, `superseded_at`.
- Dagster assets: `<source>_<verb>_<object>`, for example `taric_extract_measures`.
- Tests mirror the source path exactly: `src/pkg/a/b.py` maps to `tests/unit/pkg/a/test_b.py`.
## Error Handling

- One exception hierarchy rooted at `TariffEngineError`. Branches: `SourceError`, `ValidationError`, `TemporalError`, `ExtractionError`, `ConfigurationError`, `BudgetError`.
- Adapters translate every third-party exception into the hierarchy. No `httpx` exception escapes an adapter.
- Never swallow an exception. Either handle it, or re-raise with context added.
- Retries only on `SourceError` subclasses marked transient, using `tenacity` with exponential backoff and jitter, capped attempts, and a per-source concurrency limit.
## Configuration and Secrets

- `pydantic-settings` only, one `Settings` object, loaded once at process start and injected. No module-level environment reads.
- `.env.example` is committed and complete. `.env` is git-ignored.
- Secrets never appear in logs, traces, prompts or test fixtures.
## Logging, Tracing, Metrics

- `structlog` JSON logs, always with `run_id`, `source`, `measure_id` where applicable.
- OpenTelemetry spans on every adapter call, every LLM call and every pipeline asset. Follow the OTel GenAI semantic conventions.
- Every LLM call records model, prompt version, token counts, cost and latency. No exceptions.
- If the trace exporter fails or its quota is exhausted, the pipeline blocks. It does not continue untraced.
## LLM Usage Rules

- No prompt is inline in code. Prompts live in `prompts/<name>/<version>.md` and are loaded by identifier.
- Every LLM call is behind a typed function with a Pydantic input and a Pydantic output model.
- Model choice is configuration, never hard coded. This applies to documentation and diagrams as well as to code.
- All retrieved content, tool output and document text is untrusted input.
- Model output is never the source of truth for a legal value. It is a candidate that must pass deterministic validation and reconciliation.
- Only `adapters/llm/` imports a model vendor SDK. A vendor name elsewhere is a review failure.
- Every LLM call carries a token budget and respects both the per-run budget and the persisted monthly accumulator. A breach raises `BudgetError`.
- Client data and client identifiers are never placed in a prompt unless the data protection record says they may be.
- Every LLM call declares its workload profile, `pipeline` or `client_facing`. The profile selects the provider and the inference region. There is no silent default.
## Interface Rules

- The interface reads released values from the database. It never presents model output as a released value.
- Every displayed measure carries its CELEX identifier, its validity period, and the date the system recorded it.
- Retrieved fact and generated explanation are visually and structurally separate in the response model.
- The AI disclosure notice and the Binding Tariff Information disclaimer are components with tests.
- Every answer is logged with the measure versions it drew on, the prompt version and the model.
## Testing Standards

- `pytest`, with markers: `unit`, `integration`, `contract`, `eval`, `live`.
- Default run executes `unit` and `contract` only, fully offline and deterministic.
- Network in unit tests is blocked at the socket level.
- LLM calls in tests are replayed from recorded cassettes. `live` tests run on a schedule, never in the PR gate.
- Every source adapter has a contract test against a frozen real payload in `tests/fixtures/sources/<source>/`.
- Every bug fix starts with a failing test that reproduces it.
## Pasted Code Rules

- Every file that enters the repository is complete and runnable. No ellipses, no "rest unchanged", no `TODO` standing in for logic.
- One file per paste. Never merge two files into one block.
- Nothing is committed until `make check` passes locally on the working tree.
- If pasted code introduces a dependency, it is added with `uv add` and an ADR is written before the commit.
- If pasted code contradicts the constitution, the constitution wins.
## Public Repository Rules

- Public from the first commit. Assume every file is read by a stranger.
- No secrets, ever, including in fixtures, notebooks, example payloads and commit messages. `gitleaks` runs in `pre-commit` and CI. A leaked key is rotated first and removed second.
- No client data, no client names, no personal data in fixtures. Frozen payloads are public government data only.
- Every fixture and published dataset records the source, the retrieval date and the reuse terms.
- `LICENSE` contains Apache-2.0 from commit one.
- `README.md` states plainly what the public demo covers, what it deliberately leaves out, and why.
- Repository activity must not lapse for 60 days, or GitHub silently disables the scheduled workflows. Treat a stopped schedule as an incident.
- Trunk-based. Short-lived branches named `<type>/<openspec-change-id>-<slug>`.
- Conventional Commits. Squash merge.
- A commit or PR must reference an OpenSpec change folder. No spec, no merge.
- Self-review checklist replaces peer review while solo: read the diff in full before merging, confirm the Definition of Done, confirm the pasted code matches the spec rather than the chat conversation.
## Definition of Done

1. Spec exists and is approved in `openspec/changes/`.
2. Code passes ruff, mypy strict, import linter, licence check.
3. Unit and contract tests added and passing offline.
4. Observability added (spans, structured logs).
5. Docs updated: module README plus ADR if a choice was made.
6. Reconciliation or validation impact assessed and recorded.
7. Spec archived into `openspec/specs/` after merge.
