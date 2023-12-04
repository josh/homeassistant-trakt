"""Constants for the Trakt integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

DOMAIN: Final = "trakt"

API_URL = "https://api.trakt.tv"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=1)
