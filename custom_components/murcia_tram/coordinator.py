"""Data update coordinator for Tranvía de Murcia."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Arrival, MurciaTramClient, MurciaTramError
from .const import CONF_SAE_ID, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MurciaTramConfigEntry = ConfigEntry[MurciaTramCoordinator]

type ArrivalsByDestination = dict[str, list[Arrival]]


class MurciaTramCoordinator(DataUpdateCoordinator[ArrivalsByDestination]):
    """Fetch the next trams for one stop."""

    config_entry: MurciaTramConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MurciaTramConfigEntry,
        client: MurciaTramClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_SAE_ID]}",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.sae_id: int = config_entry.data[CONF_SAE_ID]

    async def _async_update_data(self) -> ArrivalsByDestination:
        try:
            arrivals = await self.client.async_get_arrivals(self.sae_id)
        except MurciaTramError as err:
            raise UpdateFailed(str(err)) from err

        grouped: ArrivalsByDestination = {}
        for arrival in arrivals:
            grouped.setdefault(arrival.destination, []).append(arrival)
        for items in grouped.values():
            # Known times first, soonest first; "no data" entries last.
            items.sort(key=lambda a: (a.minutes is None, a.minutes or 0))
        return grouped
