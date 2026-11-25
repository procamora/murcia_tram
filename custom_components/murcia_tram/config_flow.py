"""Config flow for Tranvía de Murcia: pick a stop from the official list."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util.location import distance
import voluptuous as vol

from .api import (
    MurciaTramClient,
    MurciaTramConnectionError,
    MurciaTramError,
    Stop,
)
from .const import CONF_SAE_ID, CONF_STOP, CONF_STOP_ID, CONF_STOP_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MurciaTramConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tranvía de Murcia (one entry per stop)."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._stops: list[Stop] | None = None

    def _client(self) -> MurciaTramClient:
        return MurciaTramClient(async_get_clientsession(self.hass))

    def _nearest_stop(self, stops: list[Stop]) -> Stop | None:
        """Return the stop closest to the Home Assistant home location."""
        home_lat, home_lon = self.hass.config.latitude, self.hass.config.longitude
        located = [s for s in stops if s.latitude is not None and s.longitude is not None]
        if not located or home_lat is None or home_lon is None:
            return None
        return min(
            located,
            key=lambda s: distance(home_lat, home_lon, s.latitude, s.longitude) or 0,
        )

    def _schema(self, stops: list[Stop]) -> vol.Schema:
        options = [
            SelectOptionDict(value=str(stop.sae_id), label=stop.name) for stop in stops
        ]
        nearest = self._nearest_stop(stops)
        key = (
            vol.Required(CONF_STOP, default=str(nearest.sae_id))
            if nearest
            else vol.Required(CONF_STOP)
        )
        return vol.Schema(
            {
                key: SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                )
            }
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the stop list and create an entry for the chosen stop."""
        errors: dict[str, str] = {}

        if self._stops is None:
            try:
                self._stops = await self._client().async_get_stops()
            except MurciaTramConnectionError:
                errors["base"] = "cannot_connect"
            except MurciaTramError:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception("Unexpected error loading the stop list")
                errors["base"] = "unknown"
            if errors:
                # Empty form: submitting it retries the download.
                return self.async_show_form(
                    step_id="user", data_schema=vol.Schema({}), errors=errors
                )
            user_input = None

        if user_input is not None and CONF_STOP in user_input:
            stop = next(
                (s for s in self._stops if str(s.sae_id) == user_input[CONF_STOP]), None
            )
            if stop is None:
                errors["base"] = "unknown_stop"
            else:
                await self.async_set_unique_id(str(stop.sae_id))
                self._abort_if_unique_id_configured()
                try:
                    await self._client().async_get_arrivals(stop.sae_id)
                except MurciaTramConnectionError:
                    errors["base"] = "cannot_connect"
                except MurciaTramError:
                    errors["base"] = "invalid_response"
                except Exception:
                    _LOGGER.exception("Unexpected error loading arrivals")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=stop.name,
                        data={
                            CONF_SAE_ID: stop.sae_id,
                            CONF_STOP_ID: stop.stop_id,
                            CONF_STOP_NAME: stop.name,
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=self._schema(self._stops), errors=errors
        )
