# Thumbnail Service

REST API that accepts image uploads, generates thumbnails (preset or custom dimensions), preserves aspect ratio, and returns metadata plus retrievable image URLs. Includes a React + TypeScript frontend for upload and preview.

## High-level design

- **API (FastAPI)**  
  - `POST /thumbnails` — upload one or more images; optional query params: `presets` (e.g. small, medium, large), `width`, `height`. Returns JSON with per-image thumbnail metadata (id, url, dimensions, preset).  
  - `GET /thumbnails/{id}` — returns the thumbnail image bytes.  
  - `GET /health` — liveness check.

- **Backend layering**  
  - **Routes** (`app/api/routes.py`) — handle multipart upload and retrieval; delegate to a thumbnail service.  
  - **Service** (`app/services/thumbnail_service.py`) — validates inputs (presets, content types, size limits), calls image utilities and storage, builds response metadata.  
  - **Image utilities** (`app/utils/image_ops.py`) — Pillow-based open/resize (aspect-ratio preserved, no upscale by default) and encode to PNG.  
  - **Storage** (`app/storage/base.py`, `app/storage/local.py`) — abstract interface for saving/reading thumbnails; local implementation persists files under a configurable root and returns URLs for retrieval.

- **Config & errors**  
  - Preset sizes, storage root, base URL, and max image size live in `app/core/config.py` (env-overridable).  
  - Domain errors (invalid image, thumbnail not found, storage failure) are raised as custom exceptions and mapped to consistent JSON error responses in `app/core/errors.py`.

- **Frontend (React + TypeScript, Vite)**  
  - Single-page UI in `frontend/`: add multiple images (append list), choose one preset per image and optional custom width/height, submit (one API call per image), then view results with thumbnails and metadata.  
  - Talks to the API via `fetch`; backend allows CORS from the dev server origin.

- **Data flow**  
  Upload → validate → for each requested size (preset and/or custom): resize (preserve aspect ratio) → save to storage → collect ids/urls/dimensions → return metadata. Retrieval: lookup by id → stream file from storage.

- **Concurrent request handling**  
  CPU-bound work (Pillow resize, file I/O for storage) runs in the event loop’s default thread pool via `run_in_executor`, so the async loop is not blocked. The server can accept and process many concurrent requests; each upload or retrieval runs its heavy work in a thread while other requests are served. For higher throughput you can run multiple uvicorn workers or scale out behind a load balancer with shared storage (e.g. S3).

## Quick start

**Backend**

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend && npm install && npm run dev
```

**Tests**

```bash
pytest
```

**CI**  
On push or pull request to `main`/`master`, GitHub Actions runs tests (see [.github/workflows/ci.yml](.github/workflows/ci.yml)): checkout → Python 3.11 → install dependencies → `pytest`.

---

API docs: `http://localhost:8000/docs`. Frontend: `http://localhost:5173`.
