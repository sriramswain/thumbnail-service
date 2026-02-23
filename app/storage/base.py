from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True)
class StoredThumbnail:
    id: str
    path: Path
    content_type: str
    original_filename: Optional[str] = None


class ThumbnailStorage(Protocol):
    def save_thumbnail(
        self,
        *,
        content: bytes,
        content_type: str,
        original_filename: Optional[str],
    ) -> StoredThumbnail:
        ...

    def open_thumbnail(self, thumbnail_id: str) -> Tuple[StoredThumbnail, bytes]:
        ...

