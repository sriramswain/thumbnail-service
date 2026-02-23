from io import BytesIO
from typing import Optional, Tuple

from PIL import Image, UnidentifiedImageError

from app.core.errors import InvalidImageError


def open_image_from_bytes(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Uploaded file is not a valid image") from exc


def resize_preserving_aspect(
    image: Image.Image,
    target_width: Optional[int],
    target_height: Optional[int],
    allow_upscale: bool = False,
) -> Tuple[Image.Image, int, int]:
    if target_width is None and target_height is None:
        raise ValueError("At least one of target_width or target_height must be set")

    orig_width, orig_height = image.size

    if target_width is not None and target_height is not None:
        width_ratio = target_width / orig_width
        height_ratio = target_height / orig_height
        ratio = min(width_ratio, height_ratio)
    elif target_width is not None:
        ratio = target_width / orig_width
    else:
        ratio = target_height / orig_height

    if not allow_upscale and ratio > 1.0:
        ratio = 1.0

    new_width = max(1, int(orig_width * ratio))
    new_height = max(1, int(orig_height * ratio))

    if new_width == orig_width and new_height == orig_height:
        return image.copy(), orig_width, orig_height

    resized = image.resize((new_width, new_height), Image.LANCZOS)
    return resized, new_width, new_height


def image_to_png_bytes(image: Image.Image) -> Tuple[bytes, str]:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue(), "image/png"

