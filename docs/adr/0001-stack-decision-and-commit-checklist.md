# ADR 0001: Stack Decision and Commit Checklist

**Date:** 2026-08-15
**Status:** Accepted

## Context

The EU Tariff Engine needs a locked technology stack before any production code is written. Every component must be chosen with three priorities in order: open source and self-hostable first, fastest path to production second, maximum auditability and compliance rigour third. The machine is Windows 11 Pro with 16 GB RAM, Intel HD Graphics 520, and no GPU.

## Decision

The following stack is locked. Changes require a new ADR.

| Layer | Choice | Licence |
|-------|--------|---------|
| Language | Python 3.13, pinned via `.python-version` | PSF |
| Packaging | uv, `uv.lock` committed | MIT |
| Agent runtime | LangGraph 1.x | MIT |
| Extraction | Pydantic AI v2 | MIT |
| Orchestration | Dagster via `dg` CLI, run natively in dev | Apache-2.0 |
| Database | PostgreSQL with pgvector | PostgreSQL Licence |
| Object storage | MinIO locally, Cloudflare R2 deployed | Apache-2.0 / proprietary |
| Parsing | pypdfium2 default, Docling for tables, managed OCR for scans | Apache-2.0 / MIT / vendor |
| Observability | Langfuse (self-hosted locally, Cloud Hobby deployed), OpenTelemetry | MIT |
| Validation | Pandera or Great Expectations, Pydantic | MIT / Apache-2.0 |
| Evaluation | promptfoo in CI, Langfuse datasets | MIT |
| Spec layer | OpenSpec CLI, terminal only, telemetry disabled | MIT |
| Model provider | Anthropic API via Pydantic AI, behind one port | N/A |
| Model tiering | Haiku 4.5 (extraction), Sonnet 5 (escalation), Opus 5 (adjudication) | N/A |
| Deployed database | Neon free plan, `aws-eu-central-1` | Proprietary (free tier) |
| Deployed scheduler | GitHub Actions cron | Proprietary (free for public repos) |
| Public demo | Static snapshot on Cloudflare Pages from R2 | Proprietary (free tier) |

### Commit Checklist (self-review, replaces peer review while solo)

Before every commit:

1. `make check` passes (lint, type, test, licence).
2. Diff read in full.
3. Commit message follows Conventional Commits and references an OpenSpec change folder.
4. No secrets, client data, or personal data anywhere in the changeset.
5. Definition of Done confirmed.
6. If a new dependency was introduced, its ADR exists and is included in the commit.

## Consequences

- All technology choices are traceable to this record.
- Any substitution (for example, swapping the embedding provider or adding a new source adapter dependency) requires a new ADR before the dependency enters `pyproject.toml`.
- The commit checklist is the quality gate while the team is one person. It becomes the PR checklist when the team grows.
