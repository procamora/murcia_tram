"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

import aiohttp
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.murcia_tram.const import (
    CONF_SAE_ID,
    CONF_STOP,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    DOMAIN,
)

from .conftest import ARRIVALS_URL, STOPS_URL


def _default(result, key: str):
    for marker in result["data_schema"].schema:
        if marker == key:
            return marker.default()
    raise AssertionError(f"{key} not in schema")


async def test_user_flow_creates_entry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    stops_payload: str,
    arrivals_payload: str,
) -> None:
    # Home next to Plaza Mayor: it must be preselected.
    hass.config.latitude, hass.config.longitude = 38.0350, -1.1440
    aioclient_mock.get(STOPS_URL, text=stops_payload)
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert _default(result, CONF_STOP) == "11"

    with patch("custom_components.murcia_tram.async_setup_entry", return_value=True) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_STOP: "11"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Plaza Mayor"
    assert result["data"] == {CONF_SAE_ID: 11, CONF_STOP_ID: 1, CONF_STOP_NAME: "Plaza Mayor"}
    assert result["result"].unique_id == "11"
    assert len(mock_setup.mock_calls) == 1

    # Every request identifies the integration instead of posing as a browser.
    for _method, _url, _data, headers in aioclient_mock.mock_calls:
        assert headers["User-Agent"].startswith("murcia_tram (+https://github.com/")


async def test_user_flow_already_configured(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, stops_payload: str
) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id="11", data={CONF_SAE_ID: 11}).add_to_hass(hass)
    aioclient_mock.get(STOPS_URL, text=stops_payload)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STOP: "11"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_cannot_connect_then_recovers(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    stops_payload: str,
    arrivals_payload: str,
) -> None:
    aioclient_mock.get(STOPS_URL, exc=aiohttp.ClientError())
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(STOPS_URL, text=stops_payload)
    aioclient_mock.post(ARRIVALS_URL, text=arrivals_payload)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch("custom_components.murcia_tram.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STOP: "8"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Campus"


async def test_user_flow_invalid_stop_list(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(STOPS_URL, text="<html>Just a moment...</html>")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["errors"] == {"base": "invalid_response"}


async def test_user_flow_arrivals_blocked(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, stops_payload: str
) -> None:
    aioclient_mock.get(STOPS_URL, text=stops_payload)
    aioclient_mock.post(ARRIVALS_URL, status=403, text="Forbidden")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STOP: "11"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
