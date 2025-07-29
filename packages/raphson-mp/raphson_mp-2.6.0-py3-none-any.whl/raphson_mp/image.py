"""
Image conversion and thumbnailing
"""

import logging
from pathlib import Path

from raphson_mp import process, settings
from raphson_mp.common.image import ImageFormat, ImageQuality

log = logging.getLogger(__name__)


async def thumbnail(
    input_path: Path, output_path: Path, img_format: ImageFormat, img_quality: ImageQuality, square: bool
):
    size = img_quality.resolution

    if square:
        thumb_filter = f"scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}"
    else:
        thumb_filter = f"scale={size}:{size}:force_original_aspect_ratio=decrease"

    if img_format is ImageFormat.WEBP:
        format_options = ["-pix_fmt", "yuv420p", "-f", "webp"]
    elif img_format is ImageFormat.JPEG:
        format_options = ["-pix_fmt", "yuvj420p", "-f", "mjpeg"]

    await process.run(
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        settings.ffmpeg_log_level,
        "-i",
        input_path.as_posix(),
        "-filter",
        thumb_filter,
        *format_options,
        output_path.as_posix(),
    )
