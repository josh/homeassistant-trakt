"""Trakt Media Player Support."""

import datetime as dt
import json
from typing import Any, Literal, cast

from aiohttp import ClientSession
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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

    coordinator = TraktWatchingUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    username = entry.data["username"]

    async_add_entities([TraktMediaPlayer(coordinator=coordinator, username=username)])


class TraktWatchingUpdateCoordinator(DataUpdateCoordinator[TraktWatchingInfo]):
    session: ClientSession
    entry: ConfigEntry
    entry_auth: AsyncConfigEntryAuth
    _cache: dict[str, Any]

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
        self.session = async_get_clientsession(self.hass)
        self.entry = entry
        self.entry_auth = hass.data[DOMAIN][entry.entry_id]
        self.tmdb_api_key = entry.data["tmdb_api_key"]
        self._cache = {}

    async def _async_update_data(self) -> TraktWatchingInfo:
        response = await self.entry_auth.async_request(
            method="GET",
            path="/users/me/watching",
        )

        if "x-ratelimit" in response.headers:
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
                if self.tmdb_api_key and data["show"]["ids"].get("tmdb"):
                    tmdb_id = data["show"]["ids"]["tmdb"]
                    season_number = data["episode"]["season"]
                    episode_number = data["episode"]["number"]
                    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}/episode/{episode_number}/images"
                    image_url = await self._async_tmdb_image_url(url, type="episode")
                    data["episode"]["tmdb_image_url"] = image_url

                if self.tmdb_api_key and data["show"]["ids"].get("tmdb"):
                    tmdb_id = data["show"]["ids"]["tmdb"]
                    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/images"
                    image_url = await self._async_tmdb_image_url(url, type="show")
                    data["show"]["tmdb_image_url"] = image_url

            elif data["type"] == "movie":
                data["movie"] = await self._async_load_extended_info(
                    type="movie",
                    id=data["movie"]["ids"]["trakt"],
                )
                if self.tmdb_api_key and data["movie"]["ids"].get("tmdb"):
                    tmdb_id = data["movie"]["ids"]["tmdb"]
                    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
                    image_url = await self._async_tmdb_image_url(url, type="movie")
                    data["movie"]["tmdb_image_url"] = image_url

            return cast(TraktWatchingInfo, data)

        if self.update_interval != dt.timedelta(minutes=5):
            LOGGER.info("Slowing down Trakt polling to 5 minutes")
            self.update_interval = dt.timedelta(minutes=5)

        return None

    async def _async_load_extended_info(
        self,
        type: Literal["episode", "show", "movie"],
        id: int,
    ) -> dict[str, Any]:
        if self._cache.get(type, {}).get("ids", {}).get("trakt") == id:
            return cast(dict[str, Any], self._cache[type])

        response = await self.entry_auth.async_request(
            method="GET",
            path=f"/{type}s/{id}?extended=full",
        )
        data = await response.json()
        self._cache[type] = data
        return cast(dict[str, Any], data)

    async def _async_tmdb_image_url(
        self,
        url: str,
        type: Literal["episode", "show", "movie"],
    ) -> str | None:
        cache_key = f"{type}_image"
        if self._cache.get(cache_key, {}).get("api_url") == url:
            return cast(str, self._cache[cache_key]["image_url"])

        response = await self.session.get(
            url,
            params={"api_key": self.tmdb_api_key},
            headers={"Accept": "application/json"},
        )
        data = await response.json()
        images = (
            data.get("backdrops", []) + data.get("posters", []) + data.get("stills", [])
        )
        if not images:
            return None

        image = images[0]
        file_path = image["file_path"]
        size = "w500"
        image_url = f"https://image.tmdb.org/t/p/{size}{file_path}"
        self._cache[cache_key] = {"api_url": url, "image_url": image_url}
        return image_url


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
    def name(self) -> str:
        """Return the device name."""
        return "Trakt"

    @property
    def unique_id(self) -> str:
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
    def media_content_type(self) -> str | None:
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
            now = dt.datetime.now(dt.UTC)
            return int((now - started_at).total_seconds())

        return None

    @property
    def media_position_updated_at(self) -> dt.datetime | None:
        """When was the position of the current playing media valid.

        Returns value from homeassistant.util.dt.utcnow().
        """
        if self.coordinator.data:
            return dt.datetime.now(dt.UTC)
        return None

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                show_title = watching["show"]["title"]
                season_number = watching["episode"]["season"]
                episode_number = watching["episode"]["number"]
                episode_title = watching["episode"]["title"]
                return f"{show_title} | S{season_number} E{episode_number} - {episode_title}"
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
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        if watching := self.coordinator.data:
            if watching["type"] == "episode":
                return (
                    watching["episode"]["tmdb_image_url"]
                    or watching["show"]["tmdb_image_url"]
                )
            elif watching["type"] == "movie":
                return watching["movie"]["tmdb_image_url"]
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
            name="Trakt",
        )
