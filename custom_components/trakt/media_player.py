"""Trakt Media Player Support."""

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

from .const import DOMAIN, LOGGER

SUPPORT_TRAKT = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Xbox media_player from a config entry."""

    LOGGER.warning("async_setup_entry entry.entry_id: %s", entry.entry_id)
    LOGGER.warning("async_setup_entry data: %s", hass.data[DOMAIN][entry.entry_id])

    async_add_entities(
        [TraktMediaPlayer()]
    )


class TraktMediaPlayer(MediaPlayerEntity):
    """Representation of an Trakt Media Player."""

    @property
    def name(self):
        """Return the device name."""
        return "TraktMediaPlayer.name"

    @property
    def unique_id(self):
        """Console device ID."""
        return "TraktMediaPlayer.unique_id"

    @property
    def state(self) -> MediaPlayerState | None:
        """State of the player."""
        return MediaPlayerState.OFF

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return SUPPORT_TRAKT

    @property
    def media_content_type(self):
        """Media content type."""
        return MediaType.TVSHOW

    @property
    def media_title(self):
        """Title of current playing media."""
        return "Game of Thrones"

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
        LOGGER.warning("async_turn_on")

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        LOGGER.warning("async_turn_off")

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, "TODO")},
            manufacturer="Trakt (device manufacturer)",
            model="Trakt (device model)",
            name="Trakt (device name)",
        )
