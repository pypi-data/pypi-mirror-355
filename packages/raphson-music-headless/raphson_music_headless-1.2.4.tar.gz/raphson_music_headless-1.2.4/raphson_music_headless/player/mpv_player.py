import asyncio
from collections.abc import Coroutine
import logging
import random
import time
from typing import cast
from typing_extensions import override
import mpv
from raphson_mp.client import RaphsonMusicClient

from raphson_music_headless.config import Config
from raphson_music_headless.downloader import Downloader
from raphson_music_headless.player import AudioPlayer


_LOGGER = logging.getLogger(__name__)  # noqa: F821


class MPVAudioPlayer(AudioPlayer):
    """
    https://pypi.org/project/python-mpv
    https://mpv.io/manual/master/#command-interface
    """

    player: mpv.MPV

    def __init__(
        self, client: RaphsonMusicClient, downloader: Downloader, config: Config
    ):
        super().__init__(client, downloader, config)

        self.player = mpv.MPV()

    @override
    async def setup(self):
        await super().setup()
        loop = asyncio.get_running_loop()

        # https://mpv.io/manual/master/#command-interface-end-file
        @self.player.event_callback("end_file")
        def on_media_end(event: mpv.MpvEvent):  # pyright: ignore[reportUnusedFunction]
            data = cast(mpv.MpvEventEndFile, event.data)
            # do not start new track when current track is intentionally aborted using stop()
            if data.reason != mpv.MpvEventEndFile.ABORTED:
                asyncio.run_coroutine_threadsafe(self.on_media_end(), loop)

    async def on_media_end(self) -> None:
        _LOGGER.info("Media ended, play next")
        tasks: list[Coroutine[None, None, None]] = []
        # save current info before it is replaced by the next track
        if self.currently_playing and self.currently_playing.track:
            path = self.currently_playing.track.path
            start_timestamp = self.start_timestamp
            tasks.append(self.client.submit_played(path, start_timestamp))
        tasks.append(self.next(retry=True))
        await asyncio.gather(*tasks)

    @override
    def stop(self) -> None:
        self.player.stop()
        self.currently_playing = None

    @override
    def pause(self) -> None:
        self.player.pause = True
        asyncio.create_task(self._submit_now_playing())

    @override
    async def play(self):
        if self.has_media():
            self.player.pause = False
            asyncio.create_task(self._submit_now_playing())
        else:
            await self.next(retry=True)

    @override
    async def next(self, *, retry: bool, force_news: bool = False) -> None:
        download = await self._get_next_track(retry=retry, force_news=force_news)
        self.currently_playing = download
        self.start_timestamp = int(time.time())

        # re-implementation of play_bytes to work around this issue:
        # https://github.com/jaseg/python-mpv/issues/292
        stream_name = random.randbytes(8).hex()
        @self.player.python_stream(stream_name)
        def reader():
            yield download.audio
            reader.unregister()  # pyright: ignore[reportFunctionMemberAccess]

        self.player.play(f"python://{stream_name}")
        self.player.wait_until_playing()
        asyncio.create_task(self._submit_now_playing())

    @override
    def has_media(self) -> bool:
        return cast(float | None, self.player.duration) is not None

    @override
    def is_playing(self) -> bool:
        return not cast(bool, self.player.pause)

    @override
    def position(self) -> int:
        position = cast(float | None, self.player.time_pos)
        if position:
            return int(position)
        else:
            return 0

    @override
    def duration(self) -> int:
        duration = cast(float | None, self.player.duration)
        if duration:
            return int(duration)
        else:
            return 0

    @override
    def seek(self, position: int):
        duration = cast(float | None, self.player.duration)
        if duration:
            self.player.seek(min(position, int(duration)), reference="absolute")

    @override
    def get_volume(self) -> float:
        try:
            volume = cast(float | None, self.player.ao_volume)
            if volume:
                return volume / 100
        except RuntimeError:
            pass
        return 0

    @override
    def set_volume(self, volume: float) -> None:
        try:
            self.player.ao_volume = volume * 100
        except RuntimeError:
            pass
