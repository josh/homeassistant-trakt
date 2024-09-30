"""API for Trakt bound to Home Assistant OAuth."""

from typing import cast

from aiohttp import ClientSession, client
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

from .const import TraktUserProfile


class AsyncConfigEntryAuth:
    """Provide Trakt authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Trakt auth."""
        self._websession = websession
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self._oauth_session.valid_token:
            await self._oauth_session.async_ensure_token_valid()
        return cast(str, self._oauth_session.token["access_token"])

    async def async_user_profile(self) -> TraktUserProfile:
        """Return the user profile."""
        response = await self.async_request(method="GET", path="/users/me")
        return cast(TraktUserProfile, await response.json())

    async def async_request(self, method: str, path: str) -> client.ClientResponse:
        implementation = cast(LocalOAuth2Implementation, self._oauth_session)
        client_id = implementation.client_id
        assert len(client_id) == 64, f"Trakt OAuth client_id not found: {client_id}"

        url = f"https://api.trakt.tv{path}"
        headers = {
            "Content-Type": "application/json",
            "trakt-api-key": client_id,
            "trakt-api-version": "2",
        }

        return await self._oauth_session.async_request(method, url, headers=headers)
