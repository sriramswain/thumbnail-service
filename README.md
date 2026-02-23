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

## Deploy on DigitalOcean

**Option A: App Platform (from GitHub)**

1. In [DigitalOcean](https://cloud.digitalocean.com/) go to **Apps** → **Create App** → choose **GitHub** and select `thumbnail-service`.
2. **Backend (API):**
   - Add a **Component** → **Web Service**.
   - Source: same repo, root. **Run command:** `uvicorn app.main:app --host 0.0.0.0 --port 8080` (App Platform often uses 8080; set **HTTP Port** to 8080 in the component).
   - **Build command:** `pip install -r requirements.txt` (or leave empty and use a Dockerfile).
   - **Env vars:** `THUMBNAIL_BASE_URL=https://your-api-url.on.digitalocean.app` (replace with the URL App Platform gives the API), and `CORS_ORIGINS=https://your-frontend-url.on.digitalocean.app` when you add a frontend.
3. **Frontend (optional):** Add another component → **Static Site** (or **Web Service** if you build with Node). Source: same repo, **Source Directory** `frontend`. Build: `npm ci && npm run build`. Output directory: `dist`. Set **CORS_ORIGINS** on the API to this app’s URL.
4. Deploy. Thumbnails are stored on the app’s filesystem; they are lost on redeploy unless you add a [Volume](https://docs.digitalocean.com/products/app-platform/how-to/manage-volumes/) or use object storage (e.g. Spaces).

**Option B: Droplet (Docker)**

1. Create a Droplet (Ubuntu). SSH in.
2. Install Docker. Clone the repo (or pull the image if you use a registry).
3. From the repo root: `docker build -t thumbnail-api . && docker run -d -p 8000:8000 -e THUMBNAIL_BASE_URL=http://YOUR_DROPLET_IP:8000 thumbnail-api`.
4. Open `http://YOUR_DROPLET_IP:8000/docs`. To serve the frontend, build it locally (`cd frontend && npm run build`), then serve the `dist/` folder with nginx or another web server on the same Droplet, and set `CORS_ORIGINS` to that URL.

**Env vars (production)**

- `THUMBNAIL_BASE_URL` — public URL of the API (used in thumbnail URLs in responses).
- `CORS_ORIGINS` — comma-separated allowed origins (e.g. your frontend URL).
- `THUMBNAIL_STORAGE_ROOT` — optional; default is `./storage` (use a volume path in App Platform if you need persistence).

---

API docs: `http://localhost:8000/docs`. Frontend: `http://localhost:5173`.
