# Thumbnail Service — Technical Overview (Code Review Talking Points)

Use this as a cheat sheet for your technical review. Walk through it in order; each section is short so you can explain it in 1–2 minutes.

---

## 1. What It Does (Elevator Pitch)

A REST API that accepts image uploads, resizes them into thumbnails (preset sizes or custom dimensions), preserves aspect ratio, and returns metadata plus a way to retrieve each thumbnail. There’s a React frontend to upload images and see results. The backend is built to handle many concurrent requests.

---

## 2. High-Level Design

**Backend (FastAPI, Python)**  
- **Routes** (`app/api/routes.py`): Two main endpoints — `POST /thumbnails` (upload + generate) and `GET /thumbnails/{id}` (retrieve image). Health at `GET /health`.  
- **Service layer** (`app/services/thumbnail_service.py`): Validates input (presets, content type, file size), calls image logic and storage, builds the JSON response. Routes stay thin; business logic lives here.  
- **Image utilities** (`app/utils/image_ops.py`): Pillow-based open, resize (aspect ratio preserved, no upscaling by default), and encode to PNG.  
- **Storage** (`app/storage/base.py`, `app/storage/local.py`): Abstract interface (save thumbnail, open by id). Local implementation writes files to disk under a configurable root. Easy to swap for S3/Spaces later.  
- **Config** (`app/core/config.py`): Presets, storage root, base URL, max file size — all env-overridable so we can change behavior without code changes.

**Frontend (React + TypeScript, Vite)**  
- Single page: add one or more images (append list), pick one preset per image and optional custom width/height, submit. One API call per image so each can have different options. Results show thumbnails and metadata (size, preset, id, link to open image).  
- Calls the API with `fetch`; backend CORS is configurable via `CORS_ORIGINS` for local and production.

**Data flow (one sentence)**  
Upload → validate → for each requested size: resize (preserve aspect ratio) → save to storage → return metadata (id, url, dimensions). Retrieval: look up by id → stream file from storage.

---

## 3. Error Handling and Validation

**Where validation happens**  
- **Service layer**: At least one image; at least one preset or custom width/height; presets must be known (small/medium/large); content type allowed (JPEG, PNG, WebP); file size under limit (e.g. 5MB).  
- **FastAPI**: Query/params (e.g. width/height > 0) and request shape.

**How errors are returned**  
- Custom exceptions in `app/core/errors.py`: `InvalidImageError`, `ThumbnailNotFoundError`, `StorageError`.  
- These are registered with FastAPI exception handlers so every error returns the same JSON shape: `{"error": {"code": "...", "message": "..."}}` with the right HTTP status (400, 404, 500). No raw tracebacks to the client; clients can rely on a consistent contract.

---

## 4. Async and Concurrency (“Handle X Concurrent Users”)

**Why it matters**  
- Resize (Pillow) and file I/O are blocking. If we ran them directly in the async event loop, one slow request would block everyone else.

**What we did**  
- In the routes we use `asyncio.run_in_executor`: the sync work (generate thumbnails, read thumbnail from storage) runs in the default thread pool. The event loop stays free to accept and schedule other requests. So we can handle many concurrent users; each request’s heavy work runs in a thread without blocking others.

**Where**  
- `POST /thumbnails`: `service.generate_thumbnails(...)` is run via `run_in_executor`.  
- `GET /thumbnails/{id}`: `service.get_thumbnail_content(id)` is run via `run_in_executor`.

---

## 5. Testing

**What we test**  
- **Image utilities** (`tests/test_image_ops.py`): Open valid image from bytes; resize with width-only and height-only and check dimensions (aspect ratio preserved).  
- **API** (`tests/test_api.py`): Health endpoint returns 200; POST with a file and presets/width returns 201 and valid JSON; GET with a returned thumbnail id returns 200 and image bytes. Tests use a temp directory for storage (monkeypatch) so we don’t touch real disk.

**How we run it**  
- `pytest` (with `PYTHONPATH=.` in CI so `app` and `app.storage` are importable).  
- CI (GitHub Actions) runs on push/PR to main: install deps, run pytest. No separate deploy step; deployment is via DigitalOcean App Platform connected to the repo.

---

## 6. Backend Details Worth Mentioning

- **Presets**: small (64×64), medium (256×256), large (1024×1024) — “up to” that size; aspect ratio preserved so one side may be smaller.  
- **Default preset**: If the client sends no preset and no custom dimensions, we use a default (e.g. medium) so a plain upload still works.  
- **Storage**: Files saved with a unique id (e.g. UUID); GET looks up by id and streams the file. Local storage is a single directory; the same interface could be implemented with S3/Spaces.  
- **CORS**: Configurable via `CORS_ORIGINS` so the same backend works for local dev and production frontend.

---

## 7. Frontend Details Worth Mentioning

- **Multiple images**: User can add files in a list (append); each row has filename, preset (single choice: small/medium/large/default), optional custom width/height, and remove.  
- **One request per image**: So each image can have different preset/size; we then combine results in the UI.  
- **Results**: For each original file we show generated thumbnails with preview, dimensions, preset/custom label, id, and “Open original thumbnail” link (that’s a GET to the backend using the returned url).  
- **Errors**: API errors (4xx/5xx) are shown in the UI (we read `error.message` or similar from the JSON body).

---

## 8. Deployment and CI

- **CI**: GitHub Actions runs pytest on push/PR; ensures we don’t break the happy path.  
- **Deploy**: DigitalOcean App Platform — repo connected, Dockerfile build, app runs the container. Env vars: `THUMBNAIL_BASE_URL` (public API URL so thumbnail links are correct), and optionally `CORS_ORIGINS` for the frontend.  
- **Docs**: README has quick start, high-level design, and deploy steps; API docs via FastAPI’s `/docs`.

---

## 9. If Asked “What Would You Improve?”

- **Storage**: Move to object storage (e.g. S3/Spaces) for persistence and scaling; the storage abstraction is already there.  
- **Auth**: Add API key or JWT if the API should be restricted.  
- **Rate limiting**: Protect the API from abuse.  
- **More tests**: Edge cases (invalid preset, non-image file, not-found id), and optionally coverage gate in CI.  
- **Frontend**: E.g. loading state per image, or retry on failure.

---

## 10. One-Liner Summary

“It’s a FastAPI backend that accepts images, generates thumbnails with presets or custom dimensions while preserving aspect ratio, returns metadata and serves thumbnails by id; blocking work runs in a thread pool so we can handle concurrent users; validation and errors are centralized and consistent; we have tests and a React frontend, and deploy on DigitalOcean with a minimal CI that runs pytest.”

Use this doc as your script: start with section 1, then 2, then drill into 3–5 (errors, async, testing) when the tech lead asks how you built it for production.
