"""Constants for the Tranvía de Murcia integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "murcia_tram"

CONF_STOP: Final = "stop"
CONF_SAE_ID: Final = "sae_id"
CONF_STOP_ID: Final = "stop_id"
CONF_STOP_NAME: Final = "stop_name"

# The official website refreshes every 60 s; do not poll faster than that.
UPDATE_INTERVAL: Final = timedelta(seconds=60)

ATTRIBUTION: Final = "Datos de tranviademurcia.es"
MANUFACTURER: Final = "Tranvía de Murcia"
WEBSITE: Final = "https://tranviademurcia.es/"

ATTR_LINE: Final = "line"
ATTR_VEHICLE: Final = "vehicle"
ATTR_TRACK: Final = "track"
