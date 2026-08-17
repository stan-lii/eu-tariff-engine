# ADR 0002: Parser Stack

**Date:** 2026-08-15
**Status:** Accepted

## Context

The system must parse EU Official Journal acts, TARIC data, and national tariff documents. Most are digital-born PDFs; some contain tables or multi-column layouts; a few are scanned.

The initial plan (v5) used PyMuPDF4LLM as the default parser. PyMuPDF and PyMuPDF4LLM are dual-licensed under GNU AGPL v3 or a paid Artifex commercial licence. Artifex states that deploying the open-source build as part of a server-based application requires disclosing the full application source under AGPL to any user interacting with it.

This project is Apache-2.0 licensed, targets real clients via a served API and interface, and the repository is public. AGPL in the runtime tree creates a licensing conflict that would surface at Phase 5 and require rework.

The constitution (added in v6) forbids AGPL, GPL, and SSPL dependencies in the runtime tree, enforced in CI.

## Decision

Replace PyMuPDF with a three-tier parser stack, all permissive:

| Role | Tool | Licence | When to use |
|------|------|---------|-------------|
| Digital-born PDF text extraction (default) | **pypdfium2** | Apache-2.0 (wraps Google PDFium, BSD-style) | Most Official Journal acts. Fast, CPU-only, no model download |
| Tables and multi-column layout | **Docling** with standard CPU pipeline | MIT | Batch job. Docling uses pypdfium2 as one of its own backends |
| Scanned or damaged documents | **Managed OCR** (provider chosen in a future ADR) | Vendor terms, recorded when chosen | No local VLM on 16 GB / no GPU hardware |

If a higher-level markdown wrapper is desired, `pdftext` (Apache-2.0, built on pypdfium2) is a candidate. Benchmark both against the Phase 5 corpus and record the choice.

The parser is a port with implementations selected by configuration. Parser name and version are part of the lineage record so a reparse under a different implementation is visible in the audit trail.

### Options Considered

| Option | Licence | Outcome |
|--------|---------|---------|
| PyMuPDF4LLM (AGPL) | AGPL-3.0 | **Rejected.** Incompatible with Apache-2.0 served product |
| PyMuPDF4LLM (commercial) | Paid Artifex licence | **Rejected.** Adds per-seat cost before revenue exists |
| pypdfium2 + Docling + managed OCR | Apache-2.0 / MIT / vendor | **Accepted.** All permissive, shared foundation |

## Consequences

- PyMuPDF and PyMuPDF4LLM must never appear in `pyproject.toml` or any dependency tree.
- CI licence check (`pip-licenses` or equivalent) fails on AGPL in the runtime tree.
- The managed OCR provider requires its own ADR when chosen, recording data processing terms and where processing happens.
- Parsing throughput on the 16 GB CPU-only machine will be measured in Phase 5 and documented in the module README.
