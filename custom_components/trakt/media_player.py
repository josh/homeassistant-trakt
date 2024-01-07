"""Trakt Media Player Support."""

import datetime as dt
import json
from typing import Literal

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import AsyncConfigEntryAuth
from .const import (
    DOMAIN,
    LOGGER,
    TraktRatelimitInfo,
    TraktWatchingInfo,
)

SUPPORT_TRAKT = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xbox media_player from a config entry."""

    entry_auth = hass.data[DOMAIN][entry.entry_id]
    user_profile = await entry_auth.async_user_profile()
    username = user_profile["username"]

    coordinator = TraktWatchingUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([TraktMediaPlayer(coordinator=coordinator, username=username)])


class TraktWatchingUpdateCoordinator(DataUpdateCoordinator[TraktWatchingInfo]):
    entry: ConfigEntry
    entry_auth: AsyncConfigEntryAuth
    _cache: dict[str, dict]

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=dt.timedelta(minutes=5),
        )
        self.entry = entry
        self.entry_auth = hass.data[DOMAIN][entry.entry_id]
        self._cache = {}

    async def _async_update_data(self) -> TraktWatchingInfo:
        response = await self.entry_auth.async_request(
            method="GET",
            path="/users/me/watching",
        )

        ratelimit: TraktRatelimitInfo = json.loads(response.headers["x-ratelimit"])
        if ratelimit["remaining"] < 60:
            LOGGER.warning("Trakt ratelimit remaining: %s", ratelimit["remaining"])
        elif ratelimit["remaining"] == 0:
            LOGGER.error("Trakt no requests remaining")

        if response.content_type == "application/json":
            if self.update_interval != dt.timedelta(minutes=1):
                LOGGER.info("Speeding up Trakt polling to 1 minute")
                self.update_interval = dt.timedelta(minutes=1)

            data = await response.json()

            if data["type"] == "episode":
                data["episode"] = await self._async_load_extended_info(
                    type="episode",
                    id=data["episode"]["ids"]["trakt"],
                )
                data["show"] = await self._async_load_extended_info(
                    type="show",
                    id=data["show"]["ids"]["trakt"],
                )

            elif data["type"] == "movie":
                data["movie"] = await self._async_load_extended_info(
                    type="movie",
                    id=data["movie"]["ids"]["trakt"],
                )

            return data

        if self.update_interval != dt.timedelta(minutes=5):
            LOGGER.info("Slowing down Trakt polling to 5 minutes")
            self.update_interval = dt.timedelta(minutes=5)

        return None

    async def _async_load_extended_info(
        self,
        type: Literal["episode", "show", "movie"],
        id: int,
    ) -> dict:
        if self._cache.get(type, {}).get("ids", {}).get("trakt") == id:
            return self._cache[type]

        response = await self.entry_auth.async_request(
            method="GET",
            path=f"/{type}s/{id}?extended=full",
        )
        data = await response.json()
        self._cache[type] = data
        return data


class TraktMediaPlayer(
    MediaPlayerEntity,
    CoordinatorEntity[TraktWatchingUpdateCoordinator],
):
    """Representation of an Trakt Media Player."""

    coordinator: TraktWatchingUpdateCoordinator
    username: str

    def __init__(
        self,
        coordinator: TraktWatchingUpdateCoordinator,
        username: str,
    ) -> None:
        """Initialize the Trakt Media Player."""
        super().__init__(coordinator)
        self.username = username

    @property
    def name(self):
        """Return the device name."""
        return f"Trakt ({self.username})"

    @property
    def unique_id(self):
        """Console device ID."""
        return self.username

    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        if self.coordinator.data:
            return MediaPlayerState.PLAYING
        else:
            return MediaPlayerState.IDLE

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return SUPPORT_TRAKT

    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return str(watching["episode"]["ids"]["trakt"])
            elif watching["type"] == "movie":
                return str(watching["movie"]["ids"]["trakt"])
        return None

    @property
    def media_content_type(self):
        """Media content type."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return MediaType.EPISODE
            elif watching["type"] == "movie":
                return MediaType.MOVIE
        return None

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return watching["episode"]["runtime"] * 60
            elif watching["type"] == "movie":
                return watching["movie"]["runtime"] * 60
        return None

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""

        if watching := self.coordinator.data:
            started_at = dt.datetime.fromisoformat(watching["started_at"])
            now = dt.datetime.now(dt.timezone.utc)
            return int((now - started_at).total_seconds())

        return None

    @property
    def media_position_updated_at(self) -> dt.datetime | None:
        """When was the position of the current playing media valid.

        Returns value from homeassistant.util.dt.utcnow().
        """
        if self.coordinator.data:
            return dt.datetime.now(dt.timezone.utc)
        return None

    @property
    def media_title(self):
        """Title of current playing media."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return f"{watching['show']['title']} - {watching['episode']['title']}"
            elif watching["type"] == "movie":
                return watching["movie"]["title"]
        return None

    @property
    def media_series_title(self) -> str | None:
        """Title of series of current playing media, TV show only."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return watching["show"]["title"]
        return None

    @property
    def media_season(self) -> str | None:
        """Season of current playing media, TV show only."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return f"Season {watching['episode']['season']}"
        return None

    @property
    def media_episode(self) -> str | None:
        """Episode of current playing media, TV show only."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return watching["episode"]["title"]
        return None

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return None

    @property
    def media_image_remotely_accessible(self) -> bool:
        """If the image url is remotely accessible."""
        return True

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        LOGGER.warning("TODO: async_turn_on")

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        LOGGER.warning("TODO: async_turn_off")

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.username)},
            manufacturer="Trakt",
            model="Trakt API",
            name=f"Trakt ({self.username})",
        )
