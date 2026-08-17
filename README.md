# EU Tariff Compliance and Validation Engine

An open-source system that ingests, parses, validates, and serves EU customs tariff data from authoritative sources including TARIC, EUR-Lex/CELLAR, and national member-state portals.

## What This Does

- Extracts tariff measures from official EU and national government sources (structured and unstructured)
- Maintains a bitemporal data model so every value can be queried as of a legal date and as known on a system date
- Validates extracted data against multiple independent sources and reconciles divergences
- Serves released measures through a versioned API with full legal citation (CELEX identifiers, validity periods, recording timestamps)
- Uses LLM-assisted extraction for document understanding, with deterministic validation gates before any value is released
## Public Demo

The public demo is a **static snapshot** of released tariff measures, published to Cloudflare Pages.

**What the demo includes:**
- A scoped slice of the Combined Nomenclature with duty rates
- CELEX identifiers and validity periods on every value
- Recording timestamps showing when the system captured each measure
**What the demo deliberately excludes:**
- Live querying or conversational AI interface (runs locally only, not publicly hosted)
- Full nomenclature coverage (the free-tier database is 0.5 GB; the snapshot covers a representative subset)
- Real-time data (the snapshot reflects the last scheduled pipeline run, not a live feed)
**Why these exclusions exist:**
- The system runs on a zero-cost deployed stack (GitHub Actions, Neon free tier, Cloudflare R2 free tier) until a client conversation starts
- EU AI Act Article 50 disclosure and marking duties apply from the moment a conversational interface goes live to anyone outside the developer's own machine
- Storage constraints on the free tier limit the publishable dataset size
## Licence

Apache-2.0. See [LICENSE](LICENSE).

The runtime dependency tree contains no AGPL, GPL, or SSPL components. This is enforced in CI.

## Technology

- **Language:** Python 3.13
- **Packaging:** uv
- **Agent runtime:** LangGraph 1.x
- **Extraction:** Pydantic AI v2
- **Orchestration:** Dagster
- **Database:** PostgreSQL with pgvector (Neon free tier in production)
- **Object storage:** Cloudflare R2 (MinIO locally)
- **Parsing:** pypdfium2 (default), Docling (tables), managed OCR (scans)
- **Observability:** Langfuse, OpenTelemetry
- **Spec layer:** OpenSpec
## Repository Structure

```
src/tariff_engine/
  domain/          Pydantic models, temporal logic, validation rules
  application/     Use cases, orchestration via abstract ports
  adapters/        Source clients, DB repos, LLM providers, parsers
    taric/         TARIC XML adapter
    cellar/        EUR-Lex/CELLAR adapter
    vies/          VAT number validation adapter
    tedb/          VAT rates adapter
    isztar/        Poland ISZTAR4 adapter
    llm/           LLM provider implementations
  interfaces/      FastAPI routes, CLI, MCP server, Dagster assets
docs/              Constitution, ADRs, code generation brief
openspec/          Specifications (source of truth for requirements)
tests/             Unit, contract, integration, eval, live test suites
prompts/           Versioned prompt templates
templates/         Module scaffolding template
```

## Data Sources

Output is informational. The legal act in EUR-Lex is authoritative over any data feed. Binding classification comes from a Binding Tariff Information (BTI) decision.

| Source | Type | Status |
|--------|------|--------|
| TARIC (DG TAXUD) | EU-wide integrated tariff | Primary |
| EUR-Lex / CELLAR | Legal acts, consolidated texts | Legal source of record |
| VIES | VAT number validation | Supporting |
| TEDB | VAT rates database | Supporting |
| Poland ISZTAR4 | National tariff (JSON API) | National expansion |
| Sweden Tullverket | National tariff (XML) | National expansion |
| Belgium TARBEL | National tariff (XML) | National expansion |

## Status

Under active development. Phase 0 (governance and repository foundation).

## Disclaimer

This system provides informational output only. It is not legal advice. The legal act published in the Official Journal of the European Union and accessible via EUR-Lex is the authoritative source for any tariff measure. Binding classification can only be obtained through a Binding Tariff Information (BTI) decision issued by a member-state customs authority.
