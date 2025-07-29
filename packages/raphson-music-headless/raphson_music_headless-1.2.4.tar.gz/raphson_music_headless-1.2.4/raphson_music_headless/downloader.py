import asyncio
import logging
import time
from collections import deque
from datetime import datetime

from aiohttp import ClientError
from raphson_mp.client import RaphsonMusicClient
from raphson_mp.client.track import DownloadedTrack
from raphson_mp.common.playlist import Playlist

from .config import Config

_LOGGER = logging.getLogger(__name__)


class Downloader:
    client: RaphsonMusicClient
    cache: dict[str, deque[DownloadedTrack]] = {}
    queue: list[DownloadedTrack] = []
    all_playlists: dict[str, Playlist] = {}
    previous_playlist: str | None = None
    enabled_playlists: list[str]
    cache_size: int
    news: DownloadedTrack | None = None
    last_news_update: int = 0

    def __init__(self, client: RaphsonMusicClient, config: Config):
        self.client = client
        self.enabled_playlists = list(config.default_playlists)
        self.cache_size = config.cache_size

    async def setup(self):
        asyncio.create_task(self._fill_cache_task())
        asyncio.create_task(self._update_playlists_task())

    async def _update_playlists_task(self):
        async def update_playlists():
            self.all_playlists = {
                playlist.name: playlist for playlist in await self.client.playlists()
            }

        while True:
            await asyncio.gather(update_playlists(), asyncio.sleep(300))

    async def _fill_cache_task(self):
        while True:
            await asyncio.gather(self.fill_cache(), asyncio.sleep(1))

    async def fill_cache(self):
        """
        Ensure cache contains enough downloaded tracks
        """
        # Only update news once every 10 minutes to prevent spam of failing requests
        if time.time() - self.last_news_update > 10 * 60:
            try:
                if not self.news:
                    # No news, update immediately
                    _LOGGER.info("downloading news")
                    self.last_news_update = int(time.time())
                    self.news = await self.client.get_news()
                    return

                # Update when new news is ready
                if datetime.now().minute == 10:
                    _LOGGER.info("Downloading news")
                    self.last_news_update = int(time.time())
                    self.news = await self.client.get_news()
                    return
            except ClientError:
                _LOGGER.warning("Failed to download news")
                return

        if len(self.enabled_playlists) == 0:
            return

        for playlist_name in self.enabled_playlists:
            if playlist_name in self.cache:
                if len(self.cache[playlist_name]) >= self.cache_size:
                    continue
            else:
                self.cache[playlist_name] = deque()

            try:
                track = await self.client.choose_track(playlist_name)
                _LOGGER.info("Downloading track: %s", track.path)
                downloaded = await track.download()
                self.cache[playlist_name].append(downloaded)
            except ClientError:
                _LOGGER.warning(
                    "Failed to download track for playlist %s",
                    playlist_name,
                    exc_info=True,
                )
                time.sleep(1)

    def select_playlist(self) -> str | None:
        """
        Choose a playlist to play a track from.
        """
        if len(self.enabled_playlists) == 0:
            _LOGGER.warning("No playlists enabled!")
            return None

        if self.previous_playlist:
            try:
                cur_index = self.enabled_playlists.index(self.previous_playlist)
                self.previous_playlist = self.enabled_playlists[
                    (cur_index + 1) % len(self.enabled_playlists)
                ]
            except ValueError:  # not in list
                self.previous_playlist = self.enabled_playlists[0]
        else:
            self.previous_playlist = self.enabled_playlists[0]

        return self.previous_playlist

    async def enqueue(self, track_path: str, front: bool = False) -> None:
        track = await self.client.get_track(track_path)
        download = await track.download()
        if front:
            self.queue.insert(0, download)
        else:
            self.queue.append(download)

    async def enqueue_news(self) -> None:
        if self.news:
            self.queue.append(self.news)

    def get_track(self) -> DownloadedTrack | None:
        """
        Get the next track to play
        """
        if self.queue:
            return self.queue.pop(0)

        playlist = self.select_playlist()
        if playlist is None:
            return None

        if playlist not in self.cache or len(self.cache[playlist]) == 0:
            return None

        return self.cache[playlist].popleft()
