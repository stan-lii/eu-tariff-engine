# System Boundary and Domain Glossary

**Status:** Approved
**Author:** Stanley
**Date:** 2026-08-16

---

## System Boundary

The EU Tariff Compliance and Validation Engine ingests, parses, validates, and serves EU customs tariff data from authoritative sources. It is an informational system. It is not a customs declaration system, it does not submit filings, and it does not issue binding classifications.

### What the system does

- Acquires tariff data from EU central sources (TARIC, EUR-Lex/CELLAR) and national member-state portals
- Parses structured data (XML, JSON, Excel) and unstructured data (PDF legal acts, HTML)
- Maintains a bitemporal data model: every value is queryable as of a legal date and as known on a system date
- Validates extracted data against multiple independent sources and reconciles divergences
- Releases measures only after passing deterministic validation gates
- Serves released measures through a versioned API with full legal citation
- Uses LLM-assisted extraction as a candidate generation step, never as a source of truth

### What the system does not do

- Issue or replace Binding Tariff Information (BTI) decisions
- Submit customs declarations on behalf of importers or exporters
- Provide legal advice
- Store or process personal data beyond what is strictly necessary for client authentication
- Replace the legal act published in the Official Journal as the authoritative source

### Authoritative sources (in order of precedence)

1. The legal act in EUR-Lex (CELEX/ELI identifier), which is the source of record
2. TARIC data (DG TAXUD), which is the operational data feed
3. National tariff portals, which add national measures (VAT, excise, national digits)
4. LLM extraction output, which is always a candidate requiring validation

---

## Domain Glossary

### Measure

A regulatory instrument that applies to goods crossing an EU border. Each measure has a type (duty, suspension, quota, anti-dumping, safeguard, prohibition, restriction), a goods scope (defined by nomenclature codes), a geographical scope, a legal basis, and a validity period. Measures are the primary entity in the data model.

### Nomenclature Code

A numeric code identifying a category of goods. The Combined Nomenclature (CN) uses 8 digits. TARIC extends this to 10 digits with two additional digits for EU measures. National tariffs may add further digits for national measures. Codes are hierarchical: chapter (2 digits), heading (4 digits), subheading (6 digits via the Harmonized System), CN subheading (8 digits), TARIC subheading (10 digits).

### Duty

A charge levied on goods at import. Types include ad valorem (percentage of customs value), specific (fixed amount per unit of quantity), compound (ad valorem plus specific), and flat per-item (such as the EUR 3 low-value consignment duty from 1 July 2026). A duty is expressed through a duty expression, which is a structured representation of the rate, its type, and the unit of measurement.

### Suspension

A temporary reduction or removal of a duty on specified goods, usually to ensure supply of materials not produced in sufficient quantity within the EU. Suspensions have a validity period and are published as Council Regulations. They are measures with a specific measure type that reduces or zeroes the normal duty.

### Quota

A tariff rate quota (TRQ) allows a specified quantity of goods to be imported at a reduced or zero duty rate. Once the quota volume is exhausted, the normal (out-of-quota) duty rate applies. Quota balances change intraday. Each quota has an order number, a volume, a unit, and a duty rate that applies within the quota.

### Validity Period

The time span during which a measure is legally in force. Defined by a start date (`valid_from`) and an optional end date (`valid_to`). An open-ended measure has no `valid_to`. Validity periods can be amended retroactively. The bitemporal model tracks both the legal validity period and the date the system recorded the information (`recorded_at`, `superseded_at`).

### Deemed Importer

Under the 2026 low-value consignment regime, platforms and distance sellers are deemed to be the importer for customs purposes when they facilitate the sale of goods valued below EUR 150 to consumers in the EU. The actual consumer is no longer treated as the importer of record. This changes who owes the customs duty and the handling fee.

### Low-Value Consignment

A consignment of goods with a value below EUR 150 shipped to a consumer in the EU. From 1 July 2026, the previous customs duty exemption for these goods was abolished. A flat EUR 3 customs duty per item now applies. A separate handling fee (level set by Commission delegated act) must be collected by member states no later than 1 November 2026. Both are temporary and remain in force until the EU Customs Data Hub is operational.

### Legal Act Reference

A pointer to the legal instrument that establishes or amends a measure. Identified by a CELEX number (the canonical EUR-Lex identifier, e.g., 32023R2658) and/or an ELI (European Legislation Identifier). Every released measure in the system must carry a legal act reference. The legal act is authoritative over any data feed.

### Reconciliation

The process of comparing extracted data against one or more independent sources to detect divergences. The system performs two-source reconciliation: extracted rates vs. the primary XML source, and extracted rates vs. the EU TARIC Excel extract. Divergences are classified as data-source errors (a bug in extraction or parsing) or legal-source errors (a discrepancy between two official sources, which is a fact worth reporting).

### Released Value

A measure version that has passed all validation gates (schema validation, business rule validation, reconciliation, evaluation thresholds) and is available for serving through the API. Released values are immutable. A correction supersedes a released value rather than modifying it, preserving the full audit trail.

### Provenance

The record of where a piece of data came from. Includes: source identifier, retrieval URL, retrieval timestamp, content hash, legal basis reference, and source licence/reuse terms. Provenance travels with the data from ingestion through to the released value and is never discarded.
