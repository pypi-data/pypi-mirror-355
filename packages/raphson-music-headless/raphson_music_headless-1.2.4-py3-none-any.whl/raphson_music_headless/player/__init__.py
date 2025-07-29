import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime

from raphson_mp.client import RaphsonMusicClient
from raphson_mp.client.track import DownloadedTrack
from raphson_mp.common.control import (
    ClientPlaying,
    ServerCommand,
    ServerNext,
    ServerPause,
    ServerPlay,
)

from raphson_music_headless.config import Config
from raphson_music_headless.downloader import Downloader

_LOGGER = logging.getLogger(__name__)


class AudioPlayer(ABC):
    downloader: "Downloader"
    client: RaphsonMusicClient
    currently_playing: DownloadedTrack | None = None
    start_timestamp: int = 0
    news: bool
    last_news: int

    def __init__(
        self, client: RaphsonMusicClient, downloader: "Downloader", config: Config
    ):
        self.client = client
        self.downloader = downloader
        self.news = config.news
        self.last_news = int(time.time())  # do not queue news right after starting

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    async def play(self) -> None:
        pass

    @abstractmethod
    async def next(self, *, retry: bool, force_news: bool = False) -> None:
        pass

    @abstractmethod
    def has_media(self) -> bool:
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        pass

    @abstractmethod
    def position(self) -> int:
        pass

    @abstractmethod
    def duration(self) -> int:
        pass

    @abstractmethod
    def seek(self, position: int) -> None:
        pass

    @abstractmethod
    def get_volume(self) -> float:
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        pass

    async def control_handler(self, command: ServerCommand):
        if isinstance(command, ServerPlay):
            await self.play()
        elif isinstance(command, ServerPause):
            self.pause()
        elif isinstance(command, ServerNext):
            await self.next(retry=False)

    async def setup(self):
        asyncio.create_task(self._now_playing_submitter())
        self.client.control_start(self.control_handler)

    async def _get_next_track(
        self, *, retry: bool, force_news: bool
    ) -> DownloadedTrack:
        if force_news:
            await self.downloader.enqueue_news()
        elif self.news:
            minute = datetime.now().minute
            # a few minutes past the hour and last news played more than 30 minutes ago?
            if minute > 11 and minute < 20 and time.time() - self.last_news > 30 * 60:
                # Attempt to download news. If it fails, next retry news won't be
                # downloaded again because last_news is updated
                self.last_news = int(time.time())
                try:
                    await self.downloader.enqueue_news()
                except Exception:
                    traceback.print_exc()

        download = self.downloader.get_track()

        if not download:
            if retry:
                _LOGGER.warning("No cached track available, trying again")
                await asyncio.sleep(1)
                return await self._get_next_track(retry=retry, force_news=force_news)
            else:
                raise ValueError("No cached track available")

        return download

    async def _submit_now_playing(self):
        # slight delay so media player can load track
        # necessary when this function is called from next(), play(), etc.
        await asyncio.sleep(0.1)

        duration = self.duration()
        if self.currently_playing and duration:
            await self.client.control_send(
                ClientPlaying(
                    track=(
                        self.currently_playing.track.path
                        if self.currently_playing.track
                        else None
                    ),
                    paused=not self.is_playing(),
                    position=self.position(),
                    duration=self.duration(),
                    volume=self.get_volume(),
                    control=True
                )
            )

    async def _now_playing_submitter(self):
        while True:
            try:
                await self._submit_now_playing()
            except Exception:
                _LOGGER.warning("Failed to submit now playing info")

            if self.is_playing():
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(30)
