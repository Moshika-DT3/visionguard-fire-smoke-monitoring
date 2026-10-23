# VisionGuard Frontend (React + Vite)

React 19 + TypeScript single-page app for the VisionGuard FastAPI backend. It mirrors the server-rendered Jinja pages and talks to the backend only through its JSON API.

## Run

```bash
# 1. Backend (from the repo root)
python -m pip install -r backend/requirements.txt   # first time only
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 2. Frontend (in a second terminal)
cd frontend_react
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000`, so the backend needs no CORS changes. To point at a different backend, set `VITE_BACKEND_URL` (see `.env.example`).

Styling is Tailwind CSS v4 only (via `@tailwindcss/vite`). `src/index.css` just imports Tailwind and defines the theme colors (`bg-navy`, `text-muted`, `border-line`, `text-fire`, ...); everything else is utility classes in the components. Shared class strings live in `src/components/styles.ts`, shared building blocks (Panel, Table, badges) in `src/components/ui.tsx` and `Badges.tsx`. For editor support, install the "Tailwind CSS IntelliSense" VS Code extension.

Other scripts: `npm run build` (type-check + production build to `dist/`), `npm run preview` (serves `dist/` with the same proxy), `npm run lint`.

## Pages

| Route | Page | APIs used |
|---|---|---|
| `/` | Dashboard: metrics, recent events, monitoring status | `GET /api/health`, `GET /api/cameras`, `GET /api/events` |
| `/cameras` | Camera Sources | `GET /api/cameras` |
| `/video-testing` | Upload, preview, and YOLO analysis | `POST /api/video-tests/upload`, `GET /api/video-tests/uploads/{video_id}`, `POST /api/video-tests/{video_id}/analyze?filename=` |
| `/incidents?type=all\|fire\|smoke` | Incident History with filter tabs | `GET /api/events` |
| `/status` | System Status | `GET /api/health` |

Dashboard, Incidents, and Status refresh every 15 seconds, so new video-test incidents appear without a reload.

The backend has no metrics or filtered-events endpoint, so dashboard counts and the incident filter are calculated in the browser, using the same rules as `MonitoringService` (see `src/api/metrics.ts`).

## Structure

```
src/
  api/        types.ts (mirrors backend/models.py), client.ts (all endpoints), metrics.ts
  hooks/      useApi.ts (fetch with abort, retry, polling)
  components/ Layout, PageHeading, Badges, States
  pages/      one file per route
  utils/      formatting helpers (UTC dates, percentages)
```

## Production

`npm run build` outputs static files to `dist/`. Serve them so `/api` reaches the FastAPI backend (same origin, or a reverse proxy) and unknown paths fall back to `index.html`. Alternatively, build with `VITE_API_BASE_URL=https://backend.example.com`, which also needs CORS enabled on the backend.
