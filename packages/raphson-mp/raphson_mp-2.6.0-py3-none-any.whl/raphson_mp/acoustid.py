import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from raphson_mp import httpclient, process, ratelimit, settings

if settings.offline_mode:
    # Module must not be imported to ensure no data is ever downloaded in offline mode.
    raise RuntimeError("Cannot use bing in offline mode")


log = logging.getLogger(__name__)


API_KEY = "rTTqI4IrbJ"


@dataclass
class Fingerprint:
    duration: int
    fingerprint_b64: str


@dataclass
class LookupResult:
    acoustid_track_id: str
    mb_recording_id: str


async def lookup(fingerprint: Fingerprint) -> AsyncIterator[LookupResult]:
    """
    Returns: musicbrainz recording id
    """
    async with ratelimit.ACOUSTID:
        async with httpclient.session() as session:
            async with session.post(
                "https://api.acoustid.org/v2/lookup",
                params={
                    "format": "json",
                    "client": API_KEY,
                    "duration": fingerprint.duration,
                    "fingerprint": fingerprint.fingerprint_b64,
                    "meta": "recordingids",
                },
            ) as response:
                json = await response.json()

    for result in json["results"]:
        if "recordings" in result:
            for recording in result["recordings"]:
                yield LookupResult(result["id"], recording["id"])


async def get_fingerprint(path: Path):
    stdout, _stderr = await process.run_output("fpcalc", "-json", path.as_posix())
    result = json.loads(stdout)
    return Fingerprint(int(result["duration"]), result["fingerprint"])
