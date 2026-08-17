# ADR 0003: TARIC Acquisition Route

**Date:** 2026-08-15
**Status:** Accepted

## Context

TARIC is the single most authoritative EU-wide tariff source. The build plan assumed Phase 3 would parse a daily TARIC XML extraction from a public endpoint. That assumption does not hold.

The Commission states that TARIC data is transmitted daily to the national administrations of EU countries. The daily XML distribution is a national administration channel, not a public developer endpoint. TARIC raw data is freely available in Excel format, but the Excel is not the full measure model.

A decision is required before the Phase 3 spec is written, because it determines what the adapter parses, what the reconciliation compares against, and which source comes first.

## Options

| Route | What you get | Cost and friction |
|-------|-------------|-------------------|
| **A. Sweden Tullverket Tariff File Distribution** | Daily XML with XSD schemas, total and incremental exports, diff files, historical and future data, national measures | Free. Requires registration. PGP encrypted, ZIP. Admin interface in Swedish. Files at `https://distr.tullverket.se/tulltaxan` |
| **B. EU-level TARIC Excel extract** | Commodity codes, descriptions, duty rates | Public, free, no registration. Not the full measure model. Reconciliation baseline only |
| **C. Another national portal (e.g. Poland ISZTAR4)** | Varies | Not re-verified. Access terms unknown |

## Decision

**Use Route A (Sweden) as the primary TARIC source, and Route B (EU Excel) as the independent reconciliation baseline.**

Two independent artefacts make the reconciliation report credible. If the answer were B alone, Phase 3's 14-day zero-divergence gate would measure a parse of an Excel file against itself, which is a weaker gate.

This means Sweden becomes the first source rather than the third in the source expansion sequence. The adapter parses Swedish XML with XSD validation. The reconciliation compares loaded rates against the EU Excel extract.

### Registration

Registration for the Swedish Tariff File Distribution:

- **Main page:** https://www.tullverket.se/en/startpage/business/applyanddeclare/tulltaxantaric/tarifffiledistributiontf.4.7df61c5915510cfe9e760d4.html
- **Files hosted at:** https://distr.tullverket.se/tulltaxan
- **Specification PDF:** Available on the main page ("Tariff File Distribution", ~1.4 MB)
- **PGP public key and XSD schemas:** Available on the main page
- **Subscription service:** Available for notifications about changes and outages (Swedish only)

Access confirmed on: **2026-08-15**. Files are publicly accessible at https://distr.tullverket.se/tulltaxan with no registration required.

## Consequences

- Phase 3 adapter targets Swedish XML format, not a generic EU XML format.
- The PGP decryption and ZIP extraction become part of the `fetch` step in the adapter contract, before persistence.
- Both the decrypted checksum and the encrypted checksum are recorded.
- The source expansion sequence changes: Sweden is source #1 (not #3).
- The reconciliation job is a two-source comparison: loaded rates vs. the XML extraction, and loaded rates vs. the EU Excel extract. Divergences between the XML and the Excel are a source-level fact worth reporting, not a bug.
- If registration is denied or delayed, fallback to Route B alone with the weaker gate stated explicitly in the reconciliation report.
