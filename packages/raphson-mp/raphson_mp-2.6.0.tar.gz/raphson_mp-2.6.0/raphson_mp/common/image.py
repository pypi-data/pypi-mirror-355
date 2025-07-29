from enum import Enum


class ImageFormat(Enum):
    WEBP = "webp"
    JPEG = "jpeg"


class ImageQuality(Enum):
    HIGH = "high"
    LOW = "low"

    @property
    def resolution(self) -> int:
        if self is ImageQuality.HIGH:
            return 1200  # 1200x1200 matches highest quality MusicBrainz cover
        elif self is ImageQuality.LOW:
            return 512
        else:
            raise ValueError()
