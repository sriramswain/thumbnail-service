import os
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from app.core.config import STORAGE_ROOT
from app.core.errors import StorageError, ThumbnailNotFoundError
from app.storage.base import StoredThumbnail, ThumbnailStorage


def _ensure_root(root: Path) -> None:
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError(f"Unable to create storage root at {root}") from exc


def _ext_from_content_type(content_type: str) -> str:
    ct = content_type.split(";")[0].strip().lower()
    if ct == "image/png":
        return "png"
    if ct in {"image/jpeg", "image/jpg"}:
        return "jpg"
    if ct == "image/webp":
        return "webp"
    return "bin"


def _content_type_from_ext(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    if ext == "png":
        return "image/png"
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext == "webp":
        return "image/webp"
    return "application/octet-stream"


class LocalThumbnailStorage(ThumbnailStorage):
    def __init__(self, root: Optional[Path] = None) -> None:
        self._root = root or STORAGE_ROOT
        _ensure_root(self._root)

    def save_thumbnail(
        self,
        *,
        content: bytes,
        content_type: str,
        original_filename: Optional[str],
    ) -> StoredThumbnail:
        thumb_id = uuid4().hex
        ext = _ext_from_content_type(content_type)
        target_path = self._root / f"{thumb_id}.{ext}"

        tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        try:
            with tmp_path.open("wb") as f:
                f.write(content)
            os.replace(tmp_path, target_path)
        except OSError as exc:
            raise StorageError(f"Failed to write thumbnail to {target_path}") from exc

        return StoredThumbnail(
            id=thumb_id,
            path=target_path,
            content_type=content_type,
            original_filename=original_filename,
        )

    def open_thumbnail(self, thumbnail_id: str) -> Tuple[StoredThumbnail, bytes]:
        candidates = list(self._root.glob(f"{thumbnail_id}.*"))
        if not candidates:
            raise ThumbnailNotFoundError(f"Thumbnail {thumbnail_id} not found")

        path = candidates[0]
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise StorageError(f"Failed to read thumbnail from {path}") from exc

        content_type = _content_type_from_ext(path.suffix)
        record = StoredThumbnail(
            id=thumbnail_id,
            path=path,
            content_type=content_type,
            original_filename=None,
        )
        return record, data

