# ADR 0004: Dagster Storage on the Deployed Runtime

**Date:** 2026-08-15
**Status:** Accepted

## Context

The deployed runtime uses GitHub Actions cron to run the Dagster pipeline. The database is Neon free plan with 0.5 GB total storage. Dagster requires storage for run history, event logs, and schedule state.

The Actions job must not put Dagster's internal storage (run storage, event log storage, schedule storage) on the same 0.5 GB Neon instance that holds the released tariff measures. Doing so would shrink the publishable dataset below what the README implies.

## Options

| Option | How it works | Storage cost | Trade-off |
|--------|-------------|-------------|-----------|
| **A (recommended)** | Dagster storage is ephemeral per Actions run, using the default SQLite instance inside the runner. Lineage evidence comes from the reconciliation report and the lineage table in Postgres, not from Dagster's own run history | Zero. Full 0.5 GB for tariff data | Dagster run history is not persisted across runs. No Dagster UI in the cloud |
| **B** | Dagster storage lives on Neon alongside tariff data | Shared 0.5 GB budget | Dagster run history persisted. Less space for measures. Dagster UI could point at Neon |

## Decision

**Option A: Ephemeral Dagster storage per Actions run.**

The 0.5 GB Neon budget is too small to share with Dagster internals. Lineage and audit evidence are provided by:

1. The **lineage table** in Postgres, linking every released value back to a raw artefact in object storage.
2. The **reconciliation report**, published into the repository after each run.
3. The **structured trace** in Langfuse, recording every pipeline step.
4. The **GitHub Actions run log**, which is retained by GitHub and provides the execution record.

Dagster's own asset lineage graph is available locally via `dg dev` for development and debugging. It is not the compliance artefact; the lineage table is.

### What this means for the Actions workflow

- The workflow runs `dg check defs` (validates definitions) then `dg launch --assets '*'` (executes the pipeline).
- Dagster uses its default local storage (SQLite in the runner's filesystem), which is discarded when the runner exits.
- `dg dev` is local only and never appears in the workflow file.
- The Dagster UI stays local until Tier 1 (first real client conversation, one small EU VPS).

## Consequences

- The full 0.5 GB Neon budget is available for tariff measures, nomenclature, and vectors.
- Dagster run history does not persist across scheduled runs. If you need to debug a past run, the evidence is the reconciliation report, the Langfuse trace, and the Actions log.
- The README and any documentation must not claim that Dagster asset lineage is itself the compliance artefact. The lineage table in Postgres is.
- If the project later moves to a paid database (Tier 2+), Option B can be reconsidered in a new ADR.
