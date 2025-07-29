import asyncio
import itertools
from collections.abc import Awaitable
from pathlib import Path
from tempfile import TemporaryDirectory

from raphson_mp import image
from raphson_mp.common.image import ImageFormat, ImageQuality


async def test_thumbnail():
    with TemporaryDirectory() as tempdir:
        input_path = Path("docs/tyrone_music.jpg")
        options = itertools.product(ImageFormat, ImageQuality, [True, False])
        tasks: list[Awaitable[None]] = []
        for img_format, img_quality, square in options:
            output_path = Path(tempdir, "output" + img_format.value + img_quality.value + str(square))
            tasks.append(image.thumbnail(input_path, output_path, img_format, img_quality, square))
        await asyncio.gather(*tasks)
