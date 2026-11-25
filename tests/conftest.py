"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.murcia_tram.api import ARRIVALS_PATH, BASE_URL, STOPS_PATH

FIXTURES = Path(__file__).parent / "fixtures"
STOPS_URL = f"{BASE_URL}{STOPS_PATH}"
ARRIVALS_URL = f"{BASE_URL}{ARRIVALS_PATH}"


def load_fixture(name: str) -> str:
    """Return a fixture file as text."""
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    return


@pytest.fixture
def stops_payload() -> str:
    return load_fixture("stops.json")


@pytest.fixture
def arrivals_payload() -> str:
    return load_fixture("arrivals_sample.xml")


@pytest.fixture
def empty_arrivals_payload() -> str:
    return load_fixture("arrivals_empty.xml")
