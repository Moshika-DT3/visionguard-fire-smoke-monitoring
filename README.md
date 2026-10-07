# VisionGuard - Fire & Smoke Monitoring

VisionGuard is a standalone, demo-ready fire and smoke monitoring application built with Python, FastAPI, and Jinja2 templates. It starts with deterministic in-memory sample data supplied by the current **Mock Detection Provider** and supports local MP4 uploads for preview and filename-only mock analysis. The baseline does not require a database, authentication, Docker, cloud services, RTSP input, or machine-learning inference.

> **Important:** The current Fire/Smoke video analysis uses deterministic mock logic for testing and demonstration purposes. It does **not** perform real machine-learning or VisionAI inference. Real VisionAI-based detection is planned for a future integration.

## Baseline capabilities

The dashboard at `/` presents the VisionGuard title, active camera count, total incident count, Fire and Smoke alert counts, operational status, and recent detection events. The application also includes camera inventory, incident history, and system-status pages with a responsive local HTML, CSS, and JavaScript interface.

The sample camera inventory includes stable source identifiers, names, locations, active or offline status, and the `sample_rtsp` source type. Sample detection events are fixed and consistently ordered, with Fire or Smoke type, source information, confidence, timestamp, severity, handling status, and stable event identifiers.

## Architecture

The application separates data acquisition from application and presentation behavior:

```text
MockDetectionProvider -> MonitoringService -> FastAPI routes -> Jinja2 pages and JSON API
```

`app/providers/base.py` defines the read-only `DetectionProvider` contract. `app/providers/mock.py` implements that contract with deterministic sample cameras and events. `app/services/monitoring.py` consumes the contract to calculate dashboard metrics, filter incidents, and build system status. Page and API routes consume `MonitoringService`, rather than importing mock data directly.

Application composition is isolated in `app/main.py`, where `MockDetectionProvider` is instantiated and supplied to `MonitoringService`. A separate `MockVideoAnalysisAdapter` from `app/services/video_analysis.py` supplies filename-only results to the Video Testing API, which adds positive results to the monitoring service as session-local incidents.

## Installation

Use a supported Python environment and install the repository's existing dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run the application

Start the development server from the repository root:

```powershell
python -m uvicorn app.main:app --reload
```

Open the dashboard at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The FastAPI-generated API documentation is also available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

For a manual team demo without automatic reload, use:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Demo flow

1. Open `/` to view the monitoring dashboard. The baseline shows three active sources out of four configured sample cameras, five total incidents, two Fire alerts, and three Smoke alerts.
2. Open `/cameras` to inspect each deterministic source, including the offline Loading Bay camera.
3. Open `/incidents` to view the full incident history. Use `/incidents?type=fire` or `/incidents?type=smoke` to view the supported filtered histories.
4. Open `/status` to inspect the VisionGuard application state and the current provider status.
5. Confirm that the current provider is displayed as **Mock Detection Provider** and that its processing state is a deterministic sample stream.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Dashboard with monitoring metrics and recent events. |
| `/cameras` | Sample camera-source inventory. |
| `/incidents` | Full detection-event history. |
| `/incidents?type=fire` | Fire-only incident history. |
| `/incidents?type=smoke` | Smoke-only incident history. |
| `/video-testing` | Local MP4 upload, browser preview, and deterministic mock analysis. |
| `/status` | Application and provider operational status. |

## JSON API

| Endpoint | Response |
| --- | --- |
| `GET /api/health` | Application status, provider status, active-source count, and total-source count. |
| `GET /api/cameras` | Deterministic camera sources with identifiers, locations, availability status, and source types. |
| `GET /api/events` | Fixed sample Fire and Smoke events, preceded by any session-created mock video incidents, newest first. |

The monitoring APIs above are read-only. Video Testing additionally supports
`POST /api/video-tests/upload`, `GET /api/video-tests/uploads/{video_id}`, and
`POST /api/video-tests/{video_id}/analyze?filename=...`; it does not create
background detection work.

## Video Testing upload lifecycle

- Open `/video-testing` to upload, preview, and run deterministic mock analysis.
- Videos are stored locally in `app/uploads/` under unique UUID-based `.mp4`
  names. This entire runtime directory is ignored by Git.
- Successful uploads remain available during the current application session.
  Repeated filenames receive separate IDs and never overwrite earlier uploads.
  Only generated UUID-named MP4 files are removed on application startup and
  graceful shutdown; startup also removes leftovers after an interrupted run.
  Unrelated files are not removed. Run a single local application process.
- The default limit is **100 MiB per file**. Optional `VIDEO_UPLOAD_MAX_BYTES`
  overrides it with a positive integer byte count at application startup.
  Request this variable for environment setup if a different limit is needed.
  The application does not load `.env` itself; the launcher must supply it.
- Uploads are copied in 1 MiB chunks rather than read entirely into memory.
  Empty files return HTTP 400; files over the limit return HTTP 413. Failed
  writes and rejected files do not retain partial output, and upload handles
  are closed. Storage errors return HTTP 500.
- Non-MP4 extensions and unsupported declared MIME types return HTTP 400.
  Validation does **not** prove the bytes contain a playable MP4: the mock
  workflow intentionally does not decode media, inspect frames, or run ML.

Analysis uses only the supplied filename, not the uploaded video content. Case-insensitive substring matching on the filename stem maps `fire_test` to Fire with 96% mock confidence, `smoke_vd` to Smoke with 89% mock confidence, and all other names to No Detection without confidence. If both patterns occur, Fire takes precedence. These values are fixed demonstration outputs, not model predictions.

A positive result creates an in-memory incident visible in the dashboard, incident history, and events API, and increases the corresponding incident and alert counts. The incident uses the current UTC timestamp and the status `New — mock video analysis`. Positive results are deduplicated by the supplied filename, case-insensitively, for the application session, even when separate uploads have different IDs. No Detection and uploading alone never create incidents. The Video Testing UI submits the original filename returned by the upload endpoint.

The size limit applies to the saved file after FastAPI parses multipart data,
not to the entire incoming HTTP request. This local demo has no total-session
disk quota, expiration timer, cloud storage, or database; restarting clears
generated videos and resets in-memory incidents.

## Mock Detection Provider

`MockDetectionProvider` is the active provider for the standalone baseline. It provides fixed in-memory data every time the application starts:

- Four sample cameras, including active and offline source states.
- Five historical detection events: two Fire events and three Smoke events.
- A provider status named `Mock Detection Provider` with an operational, ready processing state.

This deterministic behavior keeps the initial demo state repeatable. Positive Video Testing results add session-local incidents without changing the provider's fixed sample records or camera inventory; restarting restores the initial counts.

## Future VisionAI Framework integration

VisionAI Framework integration is intentionally deferred. No VisionAI Framework source code has been copied, installed, or integrated into this repository. The baseline also does not perform real RTSP processing or real fire and smoke inference.

A future `VisionAIAdapter` can implement the existing `DetectionProvider` contract in `app/providers/base.py`. That adapter would translate VisionAI Framework or RTSP/video results into the existing `CameraSource`, `DetectionEvent`, and `ProviderStatus` models. The provider selection in `app/main.py` can then change from `MockDetectionProvider` to the adapter without redesigning the monitoring service, routes, templates, dashboard metrics, or JSON API.

The intended future data flow is:

```text
RTSP or video -> VisionAI Framework package -> VisionAIAdapter -> MonitoringService -> VisionGuard pages and API
```

Uploaded-video inference would also require replacing the separate `MockVideoAnalysisAdapter` with an implementation that actually processes the saved video. Changing the monitoring provider alone does not enable real inference in Video Testing. Neither integration is implemented today.

## Baseline boundaries

This intentionally small baseline excludes databases, authentication, Docker, cloud integrations, AWS services, audio or multimodal features, random background event generation, real ML inference, and RTSP connections. It works independently through the Mock Detection Provider while retaining a clear integration boundary for a future VisionAI Framework package.
