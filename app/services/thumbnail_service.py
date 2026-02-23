from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from app.core.config import (
    DEFAULT_PRESET,
    MAX_IMAGE_BYTES,
    PRESET_SIZES,
    THUMBNAIL_BASE_URL,
    is_content_type_accepted,
)
from app.core.errors import InvalidImageError
from app.models.schemas import ImageThumbnails, ThumbnailMetadata, UploadThumbnailsResponse
from app.storage.base import ThumbnailStorage
from app.utils.image_ops import (
    image_to_png_bytes,
    open_image_from_bytes,
    resize_preserving_aspect,
)


@dataclass
class InputImage:
    filename: str
    data: bytes
    content_type: str


class ThumbnailService:
    def __init__(self, storage: ThumbnailStorage) -> None:
        self._storage = storage

    def generate_thumbnails(
        self,
        images: Iterable[InputImage],
        presets: Optional[List[str]],
        width: Optional[int],
        height: Optional[int],
    ) -> UploadThumbnailsResponse:
        images_list = list(images)
        if not images_list:
            raise InvalidImageError("At least one image must be provided")

        if (not presets or len(presets) == 0) and width is None and height is None:
            presets = [DEFAULT_PRESET]
        else:
            presets = presets or []
        unknown = [p for p in presets if p not in PRESET_SIZES]
        if unknown:
            raise InvalidImageError(f"Unknown preset(s): {', '.join(unknown)}")

        items: List[ImageThumbnails] = []
        for img in images_list:
            if len(img.data) > MAX_IMAGE_BYTES:
                raise InvalidImageError(
                    f"Image {img.filename} exceeds max size of {MAX_IMAGE_BYTES} bytes"
                )

            if not is_content_type_accepted(img.content_type):
                raise InvalidImageError(
                    f"Unsupported content type for {img.filename}: {img.content_type}"
                )

            base_image = open_image_from_bytes(img.data)
            thumbnails_meta: List[ThumbnailMetadata] = []

            for preset_name in presets:
                target_w, target_h = PRESET_SIZES[preset_name]
                resized, w, h = resize_preserving_aspect(
                    base_image, target_w, target_h
                )
                content_bytes, content_type = image_to_png_bytes(resized)
                stored = self._storage.save_thumbnail(
                    content=content_bytes,
                    content_type=content_type,
                    original_filename=img.filename,
                )
                url = f"{THUMBNAIL_BASE_URL}/thumbnails/{stored.id}"
                thumbnails_meta.append(
                    ThumbnailMetadata(
                        id=stored.id,
                        url=url,
                        width=w,
                        height=h,
                        preset=preset_name,
                        is_preset=True,
                    )
                )

            if width is not None or height is not None:
                resized, w, h = resize_preserving_aspect(
                    base_image, width, height
                )
                content_bytes, content_type = image_to_png_bytes(resized)
                stored = self._storage.save_thumbnail(
                    content=content_bytes,
                    content_type=content_type,
                    original_filename=img.filename,
                )
                url = f"{THUMBNAIL_BASE_URL}/thumbnails/{stored.id}"
                thumbnails_meta.append(
                    ThumbnailMetadata(
                        id=stored.id,
                        url=url,
                        width=w,
                        height=h,
                        preset=None,
                        is_preset=False,
                    )
                )

            items.append(
                ImageThumbnails(
                    original_filename=img.filename,
                    content_type=img.content_type,
                    thumbnails=thumbnails_meta,
                )
            )

        return UploadThumbnailsResponse(items=items)

    def get_thumbnail_content(self, thumbnail_id: str) -> Tuple[bytes, str]:
        record, data = self._storage.open_thumbnail(thumbnail_id)
        return data, record.content_type

