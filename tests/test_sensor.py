"""Tests for the arrival sensors."""

from __future__ import annotations

from datetime import timedelta

import aiohttp
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.murcia_tram.const import (
    CONF_SAE_ID,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    DOMAIN,
)

from .conftest import ARRIVALS_URL


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Plaza Mayor",
        unique_id="11",
        data={CONF_SAE_ID: 11, CONF_STOP_ID: 1, CONF_STOP_NAME: "Plaza Mayor"},
    )


def _entity_id(hass: HomeAssistant, unique_id: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id, f"no entity for {unique_id}"
    return entity_id


async def _tick(hass: HomeAssistant) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()


async def test_sensors_from_real_response(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, arrivals_payload: str
) -> None:
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expected = {
        "11_0_Campus": "7",
        "11_1_Campus": "17",
        "11_0_Estación Norte": "2",
        "11_1_Estación Norte": "6",
    }
    for unique_id, value in expected.items():
        state = hass.states.get(_entity_id(hass, unique_id))
        assert state.state == value, unique_id
        assert state.attributes["unit_of_measurement"] == "min"

    first = hass.states.get(_entity_id(hass, "11_0_Campus"))
    assert first.attributes["vehicle"] == "T001"
    assert first.attributes["line"] == "L1"
    assert first.attributes["track"] == 1
    assert first.name == "Plaza Mayor Next tram to Campus"


async def test_spanish_entity_ids(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, arrivals_payload: str
) -> None:
    await hass.config.async_update(language="es")
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert _entity_id(hass, "11_0_Campus") == ("sensor.plaza_mayor_proximo_tranvia_a_campus")
    assert _entity_id(hass, "11_1_Estación Norte") == (
        "sensor.plaza_mayor_siguiente_tranvia_a_estacion_norte"
    )
    state = hass.states.get("sensor.plaza_mayor_proximo_tranvia_a_campus")
    assert state.name == "Plaza Mayor Próximo tranvía a Campus"


async def test_no_service_and_restart(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    arrivals_payload: str,
    empty_arrivals_payload: str,
) -> None:
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = _entity_id(hass, "11_0_Campus")

    # Service ends for the night: sensors go unavailable.
    aioclient_mock.clear_requests()
    aioclient_mock.post(ARRIVALS_URL, text=empty_arrivals_payload)
    await _tick(hass)
    assert hass.states.get(eid).state == STATE_UNAVAILABLE

    # Restart during the night: the sensors are restored, still unavailable.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(eid).state == STATE_UNAVAILABLE
    assert len(er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)) == 4

    # Morning: data is back.
    aioclient_mock.clear_requests()
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    await _tick(hass)
    assert hass.states.get(eid).state == "7"


async def test_update_error_marks_unavailable(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, arrivals_payload: str
) -> None:
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    eid = _entity_id(hass, "11_0_Estación Norte")
    assert hass.states.get(eid).state == "2"

    aioclient_mock.clear_requests()
    aioclient_mock.post(ARRIVALS_URL, exc=aiohttp.ClientError())
    await _tick(hass)
    assert hass.states.get(eid).state == STATE_UNAVAILABLE


async def test_diagnostics_and_unload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, arrivals_payload: str
) -> None:
    from custom_components.murcia_tram.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["arrivals"]["Campus"][0]["minutes"] == 7

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
