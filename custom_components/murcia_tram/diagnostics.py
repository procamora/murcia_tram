"""Diagnostics for Tranvía de Murcia."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import MurciaTramConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MurciaTramConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry (no personal data is stored)."""
    coordinator = entry.runtime_data
    return {
        "entry": {"title": entry.title, "data": dict(entry.data)},
        "last_update_success": coordinator.last_update_success,
        "arrivals": {
            destination: [asdict(a) for a in arrivals]
            for destination, arrivals in (coordinator.data or {}).items()
        },
    }
