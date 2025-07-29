import logging
import random
from pathlib import Path

from raphson_mp import settings


def _contains_message(message: str):
    errors_path = Path(settings.data_dir, "errors.log")
    size = errors_path.stat().st_size
    with errors_path.open("rb") as fp:
        fp.seek(size - (len(message) + 1))
        return message in fp.read().decode()


def test_errors_file():
    logger = logging.getLogger(__name__)

    message = "test " + random.randbytes(4).hex()
    logger.warning(message)
    assert _contains_message(message)

    message = "test " + random.randbytes(4).hex()
    logger.error(message)
    assert _contains_message(message)

    message = "test " + random.randbytes(4).hex()
    logger.info(message)
    assert not _contains_message(message)
