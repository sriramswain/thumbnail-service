from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def _make_image_bytes(width: int = 100, height: int = 50, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_single_image_with_preset_and_custom_size(tmp_path, monkeypatch):
    from app.storage import local as local_storage_module

    monkeypatch.setattr(local_storage_module, "STORAGE_ROOT", tmp_path)

    image_bytes = _make_image_bytes()
    files = {"files": ("test.png", image_bytes, "image/png")}

    resp = client.post(
        "/thumbnails",
        files=files,
        params={"presets": "small", "width": 80},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) == 1
    thumbnails = data["items"][0]["thumbnails"]
    assert len(thumbnails) >= 2
    ids = [t["id"] for t in thumbnails]
    assert all(isinstance(tid, str) for tid in ids)

    thumb_id = thumbnails[0]["id"]
    get_resp = client.get(f"/thumbnails/{thumb_id}")
    assert get_resp.status_code == 200
    assert get_resp.content

