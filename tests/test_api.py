"""Tests for the response parsers (no network)."""

from __future__ import annotations

import pytest

from custom_components.murcia_tram.api import (
    MurciaTramResponseError,
    parse_arrivals,
    parse_stops,
)


def test_parse_stops(stops_payload: str) -> None:
    stops = parse_stops(stops_payload)
    assert len(stops) == 4
    stop = next(s for s in stops if s.name == "Plaza Mayor")
    assert stop.stop_id == 1
    assert stop.sae_id == 11
    assert stop.latitude == pytest.approx(38.0347)


def test_parse_arrivals_real_response(arrivals_payload: str) -> None:
    arrivals = parse_arrivals(arrivals_payload)
    assert [(a.destination, a.minutes, a.vehicle) for a in arrivals] == [
        ("Campus", 7, "T001"),
        ("Campus", 17, "T002"),
        ("Estación Norte", 2, "T001"),
        ("Estación Norte", 6, "T002"),
    ]
    assert arrivals[0].line == "L1"
    assert arrivals[0].track == 1
    assert arrivals[2].track == 2


def test_parse_arrivals_no_service(empty_arrivals_payload: str) -> None:
    assert parse_arrivals(empty_arrivals_payload) == []


def test_parse_arrivals_negative_is_none() -> None:
    xml = (
        '<ArrayOfEstimacionHoraria xmlns="http://SIV/WebServiceSIV"><EstimacionHoraria>'
        "<IdParada>11</IdParada><Linea>L1</Linea><Destino>Campus</Destino>"
        "<TiempoProximoTren>-1</TiempoProximoTren><Via>1</Via><Tranvia>T1</Tranvia>"
        "</EstimacionHoraria></ArrayOfEstimacionHoraria>"
    )
    assert parse_arrivals(xml)[0].minutes is None


@pytest.mark.parametrize(
    "payload",
    [
        "<html><body>Just a moment...</body></html>",  # Cloudflare challenge
        "not xml at all",
        "<Other/>",
    ],
)
def test_parse_arrivals_rejects_unexpected(payload: str) -> None:
    with pytest.raises(MurciaTramResponseError):
        parse_arrivals(payload)


@pytest.mark.parametrize("payload", ["<html></html>", "{}", "[]"])
def test_parse_stops_rejects_unexpected(payload: str) -> None:
    with pytest.raises(MurciaTramResponseError):
        parse_stops(payload)
