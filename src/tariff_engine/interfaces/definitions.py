"""Dagster definitions for the EU Tariff Engine pipeline.

This module is the single entry point Dagster uses to discover
all assets, jobs, schedules, and resources. It lives in the
interfaces layer because Dagster is an orchestration interface,
not domain logic.
"""

import dagster


@dagster.asset
def hello_tariff_engine() -> str:
    """Placeholder asset to verify Dagster integration.

    Replace with real pipeline assets in Phase 3.
    """
    return "Dagster is connected to the tariff engine."


defs = dagster.Definitions(
    assets=[hello_tariff_engine],
)
