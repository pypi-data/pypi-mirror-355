import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import DownloadError, YoutubeDL  # pyright: ignore[reportMissingTypeStubs]

from raphson_mp import music, scanner, settings, util
from raphson_mp.auth import User

log = logging.getLogger(__name__)


if settings.offline_mode:
    # Module must not be imported to ensure no data is ever downloaded in offline mode.
    raise RuntimeError("Cannot use downloader in offline mode")


OPTIONS = {
    "cachedir": "/tmp/yt-dlp-cache",
    "paths": {"temp": "/tmp/yt-dlp-temp"},
    "color": {"stdout": "never", "stderr": "never"},
    "format": "bestaudio",
    "noplaylist": True,
    "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "webm>ogg/mp3>mp3/mka"}],
    "default_search": "ytsearch",
}


@dataclass
class YtDone:
    status_code: int


class YtError(Exception):
    status_code: int

    def __init__(self, status_code: int):
        super().__init__()
        self.status_code = status_code


class YtdlLogger:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[str | YtDone]  # contains log strings or YtDone object to indicate yt-dlp has finished

    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.queue = asyncio.Queue()

    def debug(self, msg: str) -> None:
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith("[debug] "):
            pass
        else:
            self.info(msg)

    def info(self, msg: str) -> None:
        if self.loop and self.queue:
            asyncio.run_coroutine_threadsafe(self.queue.put(msg + "\n"), self.loop)
        log.info(msg)

    def warning(self, msg: str) -> None:
        if self.loop and self.queue:
            asyncio.run_coroutine_threadsafe(self.queue.put(msg + "\n"), self.loop)
        log.warning(msg)

    def error(self, msg: str) -> None:
        if self.loop and self.queue:
            asyncio.run_coroutine_threadsafe(self.queue.put(msg + "\n"), self.loop)
        log.error(msg)

    def done(self, status_code: int) -> None:
        if self.loop and self.queue:
            asyncio.run_coroutine_threadsafe(self.queue.put(YtDone(status_code)), self.loop)


async def download(user: User, dest: music.Playlist | Path, url: str) -> AsyncIterator[bytes]:
    dest_path = dest if isinstance(dest, Path) else dest.path
    logger = YtdlLogger()
    yt_opts = {
        **OPTIONS,
        "logger": logger,
        "outtmpl": dest_path.as_posix() + "/%(uploader)s - %(title)s.%(ext)s",
    }

    def download_thread():
        with YoutubeDL(yt_opts) as ytdl:
            try:
                status_code = ytdl.download([url])  # pyright: ignore[reportUnknownMemberType]
                logger.done(status_code)
            except DownloadError:
                logger.done(1)

    await util.create_task(asyncio.to_thread(download_thread))

    while not isinstance(log := await logger.queue.get(), YtDone):
        yield log.encode()
        logger.queue.task_done()

    if log.status_code == 0:
        yield b"Done\n"
    else:
        yield f"Failed with status code {log.status_code}".encode()

    if isinstance(dest, music.Playlist):
        await util.create_task(scanner.scan_playlist(user, dest))
