# ADR 0005: SQLAlchemy as Database Toolkit

## Status

Accepted

## Context

Phase 2 requires a bitemporal database schema for Neon Postgres.
We need a Python library for schema definition, SQL generation,
and connection management that works with Alembic for migrations.

## Decision

Use SQLAlchemy 2.0.x (stable) with Core style (Table + MetaData),
not the ORM declarative style.

Rationale:
- Domain models are Pydantic, not SQLAlchemy ORM models.
  Using Core avoids a second set of mapped classes.
- Repository classes manually map between domain models and
  database rows, which is cleaner with Core.
- Alembic (the migration tool) is built on SQLAlchemy and
  works with both Core and ORM.

## Licence

MIT. No AGPL/GPL/SSPL concerns. Safe for the runtime tree.

## Consequences

- `sqlalchemy>=2.0,<2.1` added to runtime dependencies.
- All table definitions live in `adapters/database/schema.py`.
- All SQL lives in repository classes in the adapters layer.
- The domain layer remains free of any SQLAlchemy imports.
