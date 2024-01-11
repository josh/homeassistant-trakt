"""Config flow for Trakt."""

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientSession
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

STEP_TMDB_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("tmdb_api_key"): vol.All(str, vol.Length(min=32, max=32)),
    }
)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Trakt OAuth2 authentication."""

    DOMAIN = DOMAIN
    data: dict[str, Any]

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        self.data = data

        profile = await trakt_user_profile(
            async_get_clientsession(self.hass),
            self.flow_impl.client_id,
            data["token"]["access_token"],
        )
        data["username"] = profile["username"]
        logging.info("Trakt username: %s", data["username"])

        return await self.async_step_tmdb()

    async def async_step_tmdb(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="tmdb",
                data_schema=STEP_TMDB_DATA_SCHEMA,
            )

        self.data["tmdb_api_key"] = user_input.get("tmdb_api_key", None)
        if not self.data["tmdb_api_key"]:
            self.logger.warning("No TMDB API key provided")

        return await self._create_entry()

    async def _create_entry(self) -> FlowResult:
        await self.async_set_unique_id(unique_id=self.data["username"])
        return self.async_create_entry(title=self.flow_impl.name, data=self.data)


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
