# System Flow v2

**Supersedes:** `system-flow-v1.md`
**Produced in:** Phase 0, Step 9
**Corrections applied:** All 8 defects from Appendix H of `eu-tariff-engine-build-plan-v6.md`

## Defect corrections summary

| # | Defect in v1 | Correction in v2 |
|---|-------------|------------------|
| 1 | Diagram 1: provenance is a terminal node | Provenance flows into the bitemporal store via `record_measure_version()` |
| 2 | Diagram 1: no lineage edge from released measures to raw artefact | Lineage table links released values back to raw artefacts in object storage |
| 3 | Diagram 2: daily run omits parsing, extraction, candidates, escalation | Daily run includes all stages; extraction runs as part of the daily job for new or changed documents |
| 4 | All diagrams: failure paths terminate with no recovery | Review, reprocess, and supersede loops added to every failure path |
| 5 | Diagram 5: model names hard coded | Relabelled as extraction tier, escalation tier, and adjudication tier |
| 6 | Vocabulary inconsistent across diagrams | Unified: VALIDATE, RULES, RECON, EVAL, RELEASE across all diagrams |
| 7 | Diagram 7: missing components | Redis, parse profile, pipeline/client_facing profiles, idempotency keys, token budget, reconciliation report, Article 50 disclosure added |
| 8 | Literal newlines in quoted labels | All multi-line labels use `<br/>` |

---

## Diagram 1: Source Adapter Flow

Shows the five-step adapter contract. Provenance flows into the store (defect 1 fix). Lineage links released values to raw artefacts (defect 2 fix). Parse failures enter a review loop (defect 4 fix).

```mermaid
flowchart TD
    A1["1. discover()<br/>Content hash per item"]
    A2["2. fetch(ref)<br/>Raw bytes + metadata"]
    OBJ[("Object Storage<br/>(MinIO / R2)")]
    A3["3. parse(raw)<br/>Source-specific records"]
    A4["4. map(records)<br/>Canonical domain models"]
    A5["5. provenance()<br/>Source ID, legal basis,<br/>retrieval time, licence"]
    BT[("Bitemporal Store<br/>record_measure_version()")]
    LIN[("Lineage Table<br/>released value → raw artefact")]
    PFAIL["Parse Failure<br/>Recorded per record"]
    REVIEW["Operator Review"]

    A1 --> A2
    A2 --> OBJ
    A2 --> A3
    A3 --> A4
    A3 -->|"failure"| PFAIL
    PFAIL --> REVIEW
    REVIEW -->|"fix and reprocess"| A3
    A4 --> BT
    A5 --> BT
    BT --> LIN
    LIN -->|"links back to"| OBJ
```

---

## Diagram 2: Daily Pipeline Run

The scheduled job (GitHub Actions cron on weekday mornings) runs the full pipeline. Document parsing and extraction are included when new or changed documents are detected (defect 3 fix). Every terminal path writes a heartbeat (defect 4 fix).

```mermaid
flowchart TD
    CRON["GitHub Actions Cron<br/>dg check defs<br/>dg launch --assets '*'"]
    BUDGET["Check monthly<br/>spend accumulator"]
    DISC["Discover sources<br/>Content hash comparison"]
    NOCHANGE["No changes detected"]
    FETCH["Fetch raw artefacts<br/>Store to object storage"]
    PARSE["Parse documents<br/>pypdfium2 / Docling / OCR"]
    EXTRACT["LLM Extraction<br/>(extraction tier)"]
    CANDIDATE[("Candidate Table")]
    ESCAL{"Confidence<br/>check"}
    ESCALATE["Escalation tier"]
    VALIDATE["Schema + value validation"]
    RULES["Business rule validation"]
    RECON["Reconciliation<br/>XML vs Excel (two-source)"]
    EVAL["Evaluation gate<br/>Golden set threshold"]
    RELEASE["Promote to released"]
    REPORT["Write reconciliation<br/>report to repository"]
    HEARTBEAT_OK["Heartbeat: success"]
    HEARTBEAT_NONE["Heartbeat: no changes"]
    HEARTBEAT_BLOCK["Heartbeat: blocked"]
    BLOCKED["Pipeline blocked<br/>(budget or trace failure)"]
    REJECT["Validation rejected"]
    REVIEW["Operator review"]
    NOTIFY["Failure notification"]

    CRON --> BUDGET
    BUDGET -->|"within cap"| DISC
    BUDGET -->|"cap reached<br/>or trace failure"| BLOCKED
    BLOCKED --> HEARTBEAT_BLOCK
    BLOCKED --> NOTIFY
    DISC -->|"changes found"| FETCH
    DISC -->|"no changes"| NOCHANGE
    NOCHANGE --> HEARTBEAT_NONE
    FETCH --> PARSE
    PARSE --> EXTRACT
    EXTRACT --> CANDIDATE
    CANDIDATE --> ESCAL
    ESCAL -->|"high confidence"| VALIDATE
    ESCAL -->|"low confidence"| ESCALATE
    ESCALATE --> VALIDATE
    VALIDATE --> RULES
    RULES --> RECON
    RECON --> EVAL
    EVAL -->|"pass"| RELEASE
    EVAL -->|"fail"| REJECT
    REJECT --> REVIEW
    REVIEW -->|"fix and reprocess"| EXTRACT
    REVIEW -->|"supersede"| RELEASE
    RELEASE --> REPORT
    REPORT --> HEARTBEAT_OK
```

---

## Diagram 3: Bitemporal Data Model

Shows how every value carries two time axes and how corrections work through supersession rather than mutation (defect 4 fix).

```mermaid
flowchart TD
    SRC["Source artefact<br/>(XML, PDF, Excel)"]
    PARSE["Parsed records"]
    CAND["Candidate measure version<br/>valid_from, valid_to<br/>recorded_at = now"]
    GATE["Validation + reconciliation<br/>+ eval gate"]
    REL["Released measure version<br/>Immutable once released"]
    CORR["Correction needed"]
    SUP["Supersede:<br/>set superseded_at = now<br/>on old version"]
    NEWV["New measure version<br/>recorded_at = now"]
    QUERY["Query: as of legal date D,<br/>as known on date E"]

    SRC --> PARSE
    PARSE --> CAND
    CAND --> GATE
    GATE -->|"pass"| REL
    GATE -->|"fail"| CORR
    CORR -->|"reprocess"| PARSE
    REL -->|"error discovered later"| SUP
    SUP --> NEWV
    NEWV --> GATE
    REL --> QUERY
    SUP --> QUERY
```

---

## Diagram 4: Lineage and Audit Trail

Shows the chain from raw artefact to released value. Every link is preserved and queryable (defect 2 fix).

```mermaid
flowchart LR
    RAW[("Raw artefact<br/>Object storage<br/>Checksum + ETag")]
    PARSED["Parsed output<br/>Parser name + version"]
    CAND["Candidate measure<br/>LLM model + prompt version<br/>+ token cost"]
    RELEASED["Released measure<br/>Validation report<br/>Reconciliation result"]
    TRACE["Langfuse trace<br/>Full span tree"]
    LINEAGE[("Lineage table<br/>released_id → raw_artefact_id<br/>+ parse_id + candidate_id")]
    PROV["Provenance record<br/>Source ID, legal basis,<br/>retrieval time, licence"]

    RAW --> PARSED
    PARSED --> CAND
    CAND --> RELEASED
    RAW --> LINEAGE
    PARSED --> LINEAGE
    CAND --> LINEAGE
    RELEASED --> LINEAGE
    PROV --> LINEAGE
    CAND --> TRACE
```

---

## Diagram 5: LLM Extraction and Escalation

Uses tier names, never model names (defect 5 fix). Unified vocabulary (defect 6 fix). Failure paths have recovery loops (defect 4 fix).

```mermaid
flowchart TD
    DOC["Parsed document<br/>or structured data"]
    EXT["Extraction tier<br/>(default, lowest cost)"]
    PYDANTIC["Strict Pydantic schema<br/>per measure type"]
    CONF{"Confidence +<br/>validation check"}
    ESC["Escalation tier<br/>(on low confidence<br/>or validation failure)"]
    ADJ["Adjudication tier<br/>(persistent disagreement<br/>only)"]
    CAND[("Candidate table<br/>Never written to<br/>released tables")]
    VALIDATE["Schema + value validation"]
    RULES["Business rule validation"]
    RECON["Reconciliation<br/>(two-source comparison)"]
    EVAL["Evaluation gate<br/>(golden set threshold)"]
    RELEASE["Promote to released"]
    REJECT["Rejected"]
    HITL["Human-in-the-loop<br/>LangGraph checkpoint<br/>Approval queue"]
    TOKEN["Token budget check<br/>(per-run + monthly)"]
    BUDGETFAIL["BudgetError raised<br/>Pipeline blocks"]

    DOC --> TOKEN
    TOKEN -->|"within budget"| EXT
    TOKEN -->|"budget exceeded"| BUDGETFAIL
    BUDGETFAIL -->|"operator adjusts cap"| TOKEN
    EXT --> PYDANTIC
    PYDANTIC --> CONF
    CONF -->|"high confidence,<br/>validation pass"| CAND
    CONF -->|"low confidence"| ESC
    CONF -->|"disagreement"| ADJ
    ESC --> PYDANTIC
    ADJ --> PYDANTIC
    CAND --> VALIDATE
    VALIDATE --> RULES
    RULES --> RECON
    RECON --> EVAL
    EVAL -->|"pass"| RELEASE
    EVAL -->|"fail"| REJECT
    REJECT --> HITL
    HITL -->|"approved with correction"| RELEASE
    HITL -->|"reprocess"| EXT
```

---

## Diagram 6: Validation and Release Gate

Unified vocabulary across all validation steps (defect 6 fix). Recovery paths from every rejection (defect 4 fix).

```mermaid
flowchart TD
    CAND["Candidate measure version"]
    VAL["VALIDATE<br/>Schema + value checks<br/>(Pandera / Great Expectations)"]
    RULES["RULES<br/>Rate bounds, unit consistency,<br/>period continuity,<br/>mutually exclusive types,<br/>nomenclature code validity"]
    RECON["RECON<br/>Source vs legal reconciliation<br/>Two-source comparison"]
    EVAL["EVAL<br/>Extraction accuracy vs<br/>golden set threshold"]
    RELEASE["RELEASE<br/>Measure version promoted<br/>to released tables"]
    DSE["Divergence: data-source error<br/>(bug in extraction)"]
    LSE["Divergence: legal-source error<br/>(discrepancy between officials)"]
    REJECT_V["Validation failure"]
    REJECT_E["Eval threshold not met"]
    REVIEW["Operator review"]
    REPROCESS["Reprocess from source"]
    SUPERSEDE["Supersede released value<br/>(correction path)"]
    REPORT["Reconciliation report<br/>published to repository"]

    CAND --> VAL
    VAL -->|"pass"| RULES
    VAL -->|"fail"| REJECT_V
    REJECT_V --> REVIEW
    REVIEW -->|"fix"| REPROCESS
    REPROCESS --> CAND
    RULES -->|"pass"| RECON
    RULES -->|"fail"| REJECT_V
    RECON -->|"match"| EVAL
    RECON -->|"data-source divergence"| DSE
    RECON -->|"legal-source divergence"| LSE
    DSE --> REVIEW
    LSE --> REPORT
    EVAL -->|"pass"| RELEASE
    EVAL -->|"fail"| REJECT_E
    REJECT_E --> REVIEW
    RELEASE --> REPORT
    RELEASE -->|"error found post-release"| SUPERSEDE
    SUPERSEDE -->|"new version enters"| CAND
```

---

## Diagram 7: Infrastructure and Deployment

Includes Redis, parse profile, named inference profiles, idempotency keys, token budget, reconciliation report, and Article 50 disclosure (defect 7 fix).

```mermaid
flowchart TD
    subgraph "Docker Compose Profiles"
        subgraph "core (always on)"
            PG["PostgreSQL 17+<br/>pgvector"]
            REDIS["Redis<br/>(queues, caching)"]
            MINIO["MinIO<br/>(S3-compatible<br/>object storage)"]
        end
        subgraph "obs (on demand)"
            LF["Langfuse v4<br/>(web, worker,<br/>ClickHouse, Postgres,<br/>Redis, MinIO)"]
        end
        subgraph "parse (on demand)"
            DOCLING["Docling batch<br/>container (CPU)"]
        end
    end

    subgraph "Application (native, not containerised)"
        DAGSTER["Dagster<br/>dg dev (local)<br/>dg launch (deployed)"]
        FASTAPI["FastAPI<br/>versioned routes /v1/<br/>SSE streaming"]
        IDEM["Idempotency keys<br/>on every pipeline step"]
        BUDGET["Token budget<br/>per-run + monthly<br/>accumulator"]
    end

    subgraph "Inference Profiles"
        PIPE["pipeline profile<br/>Default Anthropic route<br/>Public tariff data only"]
        CLIENT["client_facing profile<br/>EU via Bedrock<br/>Client data"]
    end

    subgraph "Interface"
        UI["Client interface"]
        ART50["Article 50<br/>AI disclosure notice"]
        BTI["BTI disclaimer"]
        CITE["CELEX + validity<br/>on every value"]
        RECON_RPT["Reconciliation report"]
    end

    subgraph "Deployed Stack (zero cost)"
        NEON["Neon free plan<br/>aws-eu-central-1<br/>0.5 GB"]
        R2["Cloudflare R2<br/>EU jurisdiction bucket<br/>10 GB"]
        LFC["Langfuse Cloud Hobby<br/>50k units/month"]
        GHA["GitHub Actions cron<br/>Weekday mornings"]
        PAGES["Cloudflare Pages<br/>Static demo snapshot"]
    end

    DAGSTER --> PG
    DAGSTER --> REDIS
    DAGSTER --> MINIO
    DAGSTER --> IDEM
    DAGSTER --> BUDGET
    FASTAPI --> PG
    FASTAPI --> REDIS
    FASTAPI --> PIPE
    FASTAPI --> CLIENT
    UI --> FASTAPI
    UI --> ART50
    UI --> BTI
    UI --> CITE
    UI --> RECON_RPT
    GHA -->|"deployed"| NEON
    GHA -->|"deployed"| R2
    GHA -->|"deployed"| LFC
    GHA -->|"snapshot"| PAGES
```

---

## Vocabulary reference

Consistent terms used across all diagrams (defect 6 fix):

| Term | Meaning |
|------|---------|
| VALIDATE | Schema and value validation (Pandera / Pydantic) |
| RULES | Business rule validation (rate bounds, period continuity, etc.) |
| RECON | Source vs legal reconciliation (two-source comparison) |
| EVAL | Evaluation gate (golden set accuracy threshold) |
| RELEASE | Promotion from candidate to released table |
| SUPERSEDE | Correction of a released value (append new version, mark old as superseded) |
| CANDIDATE | Measure version awaiting validation (never served to clients) |
| REVIEW | Operator review queue with a documented exit path |
| Extraction tier | Default LLM tier (lowest cost, configured in Settings) |
| Escalation tier | Used on low confidence or validation failure |
| Adjudication tier | Used only for persistent disagreement |
