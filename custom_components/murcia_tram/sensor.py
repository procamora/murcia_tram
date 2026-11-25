"""Sensors with the minutes until the next trams at a stop."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Arrival
from .const import (
    ATTR_LINE,
    ATTR_TRACK,
    ATTR_VEHICLE,
    ATTRIBUTION,
    CONF_SAE_ID,
    CONF_STOP_NAME,
    DOMAIN,
    MANUFACTURER,
    WEBSITE,
)
from .coordinator import MurciaTramConfigEntry, MurciaTramCoordinator

PARALLEL_UPDATES = 0

# rank 0 = next tram, rank 1 = the one after it (the service gives two).
RANK_TRANSLATION_KEYS: dict[int, str] = {0: "next_tram", 1: "second_tram"}


def _unique_id(sae_id: int, rank: int, destination: str) -> str:
    return f"{sae_id}_{rank}_{destination}"


def _destination_from_unique_id(sae_id: int, unique_id: str) -> str | None:
    prefix, _, rest = unique_id.partition("_")
    if prefix != str(sae_id):
        return None
    rank, _, destination = rest.partition("_")
    if not rank.isdigit() or not destination:
        return None
    return destination


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MurciaTramConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create sensors for every destination served at the stop.

    Destinations are discovered from the data, so the integration works for any
    stop and line without hard-coding the network. Destinations seen before are
    restored from the entity registry, so the sensors still exist (unavailable)
    after a restart at night when there is no service.
    """
    coordinator = entry.runtime_data
    sae_id: int = entry.data[CONF_SAE_ID]
    known: set[str] = set()

    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        destination = _destination_from_unique_id(sae_id, reg_entry.unique_id)
        if destination:
            known.add(destination)

    async_add_entities(
        TranviaArrivalSensor(coordinator, destination, rank)
        for destination in sorted(known)
        for rank in RANK_TRANSLATION_KEYS
    )

    @callback
    def _async_add_new_destinations() -> None:
        new = [d for d in (coordinator.data or {}) if d not in known]
        if not new:
            return
        known.update(new)
        async_add_entities(
            TranviaArrivalSensor(coordinator, destination, rank)
            for destination in new
            for rank in RANK_TRANSLATION_KEYS
        )

    _async_add_new_destinations()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_destinations))


class TranviaArrivalSensor(CoordinatorEntity[MurciaTramCoordinator], SensorEntity):
    """Minutes until the next (or second) tram towards one destination."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:tram"

    def __init__(self, coordinator: MurciaTramCoordinator, destination: str, rank: int) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        sae_id: int = entry.data[CONF_SAE_ID]
        self._destination = destination
        self._rank = rank
        self._attr_unique_id = _unique_id(sae_id, rank, destination)
        self._attr_translation_key = RANK_TRANSLATION_KEYS[rank]
        self._attr_translation_placeholders = {"destination": destination}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(sae_id))},
            name=entry.data.get(CONF_STOP_NAME, entry.title),
            manufacturer=MANUFACTURER,
            model="Parada",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=WEBSITE,
        )

    @property
    def _arrival(self) -> Arrival | None:
        arrivals = (self.coordinator.data or {}).get(self._destination, [])
        if len(arrivals) <= self._rank:
            return None
        return arrivals[self._rank]

    @property
    def available(self) -> bool:
        arrival = self._arrival
        return super().available and arrival is not None and arrival.minutes is not None

    @property
    def native_value(self) -> int | None:
        arrival = self._arrival
        return arrival.minutes if arrival else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        arrival = self._arrival
        if arrival is None:
            return None
        return {
            ATTR_LINE: arrival.line,
            ATTR_VEHICLE: arrival.vehicle,
            ATTR_TRACK: arrival.track,
        }
