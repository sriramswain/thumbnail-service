import os
from pathlib import Path
from typing import Dict, Tuple


BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Where generated thumbnails are stored on disk.
STORAGE_ROOT: Path = Path(
    os.getenv("THUMBNAIL_STORAGE_ROOT", BASE_DIR / "storage")
)

# Base URL for building thumbnail URLs in responses.
THUMBNAIL_BASE_URL: str = os.getenv(
    "THUMBNAIL_BASE_URL", "http://localhost:8000"
)

# Maximum accepted image size in bytes (default: 5 MiB).
MAX_IMAGE_BYTES: int = int(
    os.getenv("THUMBNAIL_MAX_IMAGE_BYTES", str(5 * 1024 * 1024))
)

# Supported presets and their target (width, height).
PRESET_SIZES: Dict[str, Tuple[int, int]] = {
    "small": (64, 64),
    "medium": (256, 256),
    "large": (1024, 1024),
}

# Preset used when the client does not specify presets or custom dimensions.
DEFAULT_PRESET: str = os.getenv("THUMBNAIL_DEFAULT_PRESET", "medium")

# Accepted content types for uploads.
ACCEPTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def is_content_type_accepted(content_type: str) -> bool:
    return content_type.split(";")[0].strip().lower() in ACCEPTED_CONTENT_TYPES

