from io import BytesIO

from PIL import Image

from app.utils.image_ops import open_image_from_bytes, resize_preserving_aspect


def create_test_image(width: int, height: int, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_open_image_from_bytes_valid():
    data = create_test_image(100, 50)
    image = open_image_from_bytes(data)
    assert image.size == (100, 50)


def test_resize_preserving_aspect_width_only():
    data = create_test_image(200, 100)
    image = open_image_from_bytes(data)

    resized, w, h = resize_preserving_aspect(image, target_width=100, target_height=None)

    assert (w, h) == resized.size
    assert w == 100
    assert h == 50


def test_resize_preserving_aspect_height_only():
    data = create_test_image(200, 100)
    image = open_image_from_bytes(data)

    resized, w, h = resize_preserving_aspect(image, target_width=None, target_height=25)

    assert (w, h) == resized.size
    assert h == 25
    assert w == 50

