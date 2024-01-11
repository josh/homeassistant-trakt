"""Config flow for Trakt."""

import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Trakt OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        profile = await trakt_user_profile(
            async_get_clientsession(self.hass),
            self.flow_impl.client_id,
            data["token"]["access_token"],
        )
        data["username"] = profile["username"]

        return await super().async_oauth_create_entry(data)


async def trakt_user_profile(
    session: ClientSession,
    client_id: str,
    access_token: str,
) -> dict:
    url = "https://api.trakt.tv/users/me"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-key": client_id,
        "trakt-api-version": "2",
        "Authorization": f"Bearer {access_token}",
    }
    response = await session.get(url, headers=headers)
    return await response.json()
