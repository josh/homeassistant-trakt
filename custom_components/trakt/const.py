"""Constants for the Trakt integration."""

import logging
from datetime import timedelta
from typing import Final, Literal, TypedDict

DOMAIN: Final = "trakt"

API_URL = "https://api.trakt.tv"

OAUTH2_AUTHORIZE = "https://api.trakt.tv/oauth/authorize"
OAUTH2_TOKEN = "https://api.trakt.tv/oauth/token"

LOGGER = logging.getLogger(__package__)
SCAN_INTERVAL = timedelta(minutes=1)


class TraktUserIDs(TypedDict):
    slug: str


class TraktUserProfile(TypedDict):
    username: str
    private: bool
    name: str
    vip: bool
    vip_ep: bool
    ids: TraktUserIDs


class TraktEpisodeIDs(TypedDict):
    trakt: int
    slug: str


class TraktEpisode(TypedDict):
    season: int
    number: int
    title: str
    ids: TraktEpisodeIDs


class TraktShowIDs(TypedDict):
    trakt: int
    slug: str


class TraktShow(TypedDict):
    title: str
    year: int
    ids: TraktShowIDs


class TraktMovieIDs(TypedDict):
    trakt: int
    slug: str


class TraktMovie(TypedDict):
    title: str
    year: int
    ids: TraktMovieIDs


class TraktWatchingEpisode(TypedDict):
    expires_at: str
    started_at: str
    action: Literal["scrobble", "checkin"]
    type: Literal["episode"]
    episode: TraktEpisode
    show: TraktShow


class TraktWatchingMovie(TypedDict):
    expires_at: str
    started_at: str
    action: Literal["scrobble", "checkin"]
    type: Literal["movie"]
    movie: TraktMovie


TraktWatchingInfo = TraktWatchingEpisode | TraktWatchingMovie | None


class TraktRatelimitInfo(TypedDict):
    name: str
    period: int
    limit: int
    remaining: int
    until: str
