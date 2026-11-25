"""Client for the arrival times published on tranviademurcia.es.

This module has no Home Assistant imports on purpose, so it can be moved to
its own PyPI package later (a requirement for a core integration).

Endpoints (the same ones the official website uses on every stop page):

* ``GET  /api-horarios/get_paradas`` -> JSON list of stops.
* ``POST /webservicecall.php`` with ``idParada=<sae_id>&via=0`` -> XML with the
  next two trams per direction (``EstimacionHoraria`` elements).
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
import xml.etree.ElementTree as ET

import aiohttp

BASE_URL = "https://tranviademurcia.es"
STOPS_PATH = "/api-horarios/get_paradas"
ARRIVALS_PATH = "/webservicecall.php"

# Identify the integration honestly so the operator can see who is calling and
# how to get in touch. Requests are infrequent (one per stop per minute).
USER_AGENT = "murcia_tram (+https://github.com/procamora/murcia_tram; Home Assistant integration)"
DEFAULT_TIMEOUT = 15
MAX_RESPONSE_BYTES = 512 * 1024


class MurciaTramError(Exception):
    """Base error for this client."""


class MurciaTramConnectionError(MurciaTramError):
    """The website could not be reached or returned an HTTP error."""


class MurciaTramResponseError(MurciaTramError):
    """The website answered with something we could not understand."""


@dataclass(frozen=True, slots=True)
class Stop:
    """A tram stop."""

    stop_id: int
    """Position of the stop on the line (``id`` in the API)."""
    sae_id: int
    """Identifier used by the real-time service (``saeid`` in the API)."""
    name: str
    latitude: float | None
    longitude: float | None
    fare_zone: str | None


@dataclass(frozen=True, slots=True)
class Arrival:
    """An estimated arrival at a stop."""

    sae_id: int | None
    line: str | None
    destination: str
    minutes: int | None
    """Minutes until the tram arrives, ``None`` when the service has no data."""
    track: int | None
    vehicle: str | None


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_stops(payload: str) -> list[Stop]:
    """Parse the ``get_paradas`` response."""
    try:
        data = json.loads(payload)
    except ValueError as err:
        raise MurciaTramResponseError("Stop list is not valid JSON") from err
    if not isinstance(data, list):
        raise MurciaTramResponseError("Stop list has an unexpected format")

    stops: list[Stop] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        stop_id = _to_int(item.get("id"))
        sae_id = _to_int(item.get("saeid"))
        name = str(item.get("nombre") or "").strip()
        if stop_id is None or sae_id is None or not name:
            continue
        stops.append(
            Stop(
                stop_id=stop_id,
                sae_id=sae_id,
                name=name,
                latitude=_to_float(item.get("lat")),
                longitude=_to_float(item.get("lng")),
                fare_zone=item.get("tarifa") or None,
            )
        )
    if not stops:
        raise MurciaTramResponseError("Stop list is empty")
    return stops


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_arrivals(payload: str) -> list[Arrival]:
    """Parse the ``webservicecall.php`` XML response.

    An empty ``ArrayOfEstimacionHoraria`` (no service) yields an empty list.
    Negative times mean "no information" and are returned as ``None``.
    """
    try:
        root = ET.fromstring(payload.strip())
    except ET.ParseError as err:
        raise MurciaTramResponseError("Arrival data is not valid XML") from err
    if _local_name(root.tag) != "ArrayOfEstimacionHoraria":
        raise MurciaTramResponseError(
            f"Unexpected XML root element: {_local_name(root.tag)}"
        )

    arrivals: list[Arrival] = []
    for element in root:
        if _local_name(element.tag) != "EstimacionHoraria":
            continue
        fields = {_local_name(child.tag): (child.text or "").strip() for child in element}
        destination = fields.get("Destino", "")
        if not destination:
            continue
        minutes = _to_int(fields.get("TiempoProximoTren"))
        arrivals.append(
            Arrival(
                sae_id=_to_int(fields.get("IdParada")),
                line=fields.get("Linea") or None,
                destination=destination,
                minutes=minutes if minutes is not None and minutes >= 0 else None,
                track=_to_int(fields.get("Via")),
                vehicle=fields.get("Tranvia") or None,
            )
        )
    return arrivals


class MurciaTramClient:
    """Async client for tranviademurcia.es."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _request(self, method: str, path: str, **kwargs: Any) -> str:
        headers = {"User-Agent": USER_AGENT, **kwargs.pop("headers", {})}
        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            ) as response:
                if response.status != 200:
                    raise MurciaTramConnectionError(
                        f"HTTP {response.status} from {path}"
                    )
                body = await response.content.read(MAX_RESPONSE_BYTES + 1)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise MurciaTramConnectionError(f"Error calling {path}: {err}") from err
        if len(body) > MAX_RESPONSE_BYTES:
            raise MurciaTramResponseError(f"Response from {path} is too large")
        return body.decode("utf-8", errors="replace")

    async def async_get_stops(self) -> list[Stop]:
        """Return every stop of the network."""
        return parse_stops(await self._request("GET", STOPS_PATH))

    async def async_get_arrivals(self, sae_id: int) -> list[Arrival]:
        """Return the next arrivals for a stop (both directions)."""
        payload = await self._request(
            "POST",
            ARRIVALS_PATH,
            data={"idParada": str(sae_id), "via": "0"},
        )
        return parse_arrivals(payload)
