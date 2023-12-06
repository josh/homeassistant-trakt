"""Constants for the Trakt integration."""

import logging
from datetime import timedelta
from typing import Final

DOMAIN: Final = "trakt"

API_URL = "https://api.trakt.tv"

OAUTH2_AUTHORIZE = "https://api.trakt.tv/oauth/authorize"
OAUTH2_TOKEN = "https://api.trakt.tv/oauth/token"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=1)
