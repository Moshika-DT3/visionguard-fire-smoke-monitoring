# VisionGuard - Fire & Smoke Monitoring

VisionGuard is a standalone fire and smoke monitoring application built with Python, FastAPI, and Jinja2 templates. It uses deterministic in-memory sample data for the monitoring dashboard and real YOLO inference for uploaded MP4 video analysis. The baseline does not require a database, authentication, Docker, cloud services, or RTSP input.

## Baseline capabilities

The dashboard at `/` presents the VisionGuard title, active camera count, total incident count, Fire and Smoke alert counts, operational status, and recent detection events. The application also includes camera inventory, incident history, system-status pages, and a responsive local HTML, CSS, and JavaScript interface.

The sample camera inventory includes stable source identifiers, names, locations, active or offline status, and the `sample_rtsp` source type. Sample detection events are fixed and consistently ordered, with Fire or Smoke type, source information, confidence, timestamp, severity, handling status, and stable event identifiers.

## Architecture

The application separates data acquisition, analysis, and presentation behavior:

```text
MockDetectionProvider -> MonitoringService -> FastAPI routes -> Jinja2 pages and JSON API
Uploaded MP4 -> YoloVideoAnalysisAdapter -> Video Testing API -> MonitoringService
```

`app/providers/base.py` defines the read-only `DetectionProvider` contract. `app/providers/mock.py` implements that contract with deterministic sample cameras and events. `app/services/monitoring.py` consumes the contract to calculate dashboard metrics, filter incidents, and build system status. Page and API routes consume `MonitoringService`, rather than importing mock data directly.

Application composition is isolated in `app/main.py`, where `MockDetectionProvider` is instantiated and supplied to `MonitoringService`. Uploaded video analysis is handled separately by `YoloVideoAnalysisAdapter` in `app/services/video_analysis.py`. Successful Fire and Smoke results are added to the monitoring service as session-local incidents.

## Installation

Use a supported Python environment and install the repository's dependencies:

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
5. Open `/video-testing`, upload an MP4, preview it in the browser, and select **Run Analysis**.
6. Review the YOLO result. A Fire or Smoke result creates a session-local incident visible in the dashboard and incident history; No Detection does not create an incident.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Dashboard with monitoring metrics and recent events. |
| `/cameras` | Sample camera-source inventory. |
| `/incidents` | Full detection-event history. |
| `/incidents?type=fire` | Fire-only incident history. |
| `/incidents?type=smoke` | Smoke-only incident history. |
| `/video-testing` | Local MP4 upload, browser preview, and YOLO video analysis. |
| `/status` | Application and provider operational status. |

## JSON API

| Endpoint | Response |
| --- | --- |
| `GET /api/health` | Application status, provider status, active-source count, and total-source count. |
| `GET /api/cameras` | Deterministic camera sources with identifiers, locations, availability status, and source types. |
| `GET /api/events` | Fixed sample Fire and Smoke events, preceded by any session-created video-analysis incidents, newest first. |

The monitoring APIs above are read-only. Video Testing additionally supports
`POST /api/video-tests/upload`, `GET /api/video-tests/uploads/{video_id}`, and
`POST /api/video-tests/{video_id}/analyze?filename=...`; it does not create
background detection work.

## Video Testing upload lifecycle

- Open `/video-testing` to upload, preview, and analyze an MP4 using YOLO.
- Videos are stored locally in `app/uploads/` under unique UUID-based `.mp4`
  names. This entire runtime directory is ignored by Git.
- Successful uploads remain available during the current application session.
  Repeated filenames receive separate IDs and never overwrite earlier uploads.
  Only generated UUID-named MP4 files are removed on application startup and
  graceful shutdown; startup also removes leftovers after an interrupted run.
  Unrelated files are not removed. Run a single local application process.
- There is **no application-level video file-size limit**. Larger MP4 uploads,
  including 167 MB files, are accepted subject to available local storage and
  any external hosting/proxy constraints. The former `VIDEO_UPLOAD_MAX_BYTES`
  setting is no longer used.
- Uploads are copied in 1 MiB chunks rather than read entirely into memory.
  This is a copy-buffer size, not a maximum file size. Empty files return HTTP
  400. Failed writes and rejected files do not retain partial output, and
  upload handles are closed. Storage errors return HTTP 500.
- Non-MP4 extensions and unsupported declared MIME types return HTTP 400.
  Validation does **not** prove the bytes contain a playable MP4; YOLO
  inference reports an analysis error if the uploaded video cannot be decoded.

## YOLO video analysis

Video Testing uses `YoloVideoAnalysisAdapter` and the Ultralytics YOLO runtime
to inspect the frames of the uploaded video. The adapter lazily loads and
caches the `fire_smoke_yolov8n.pt` checkpoint from:

```text
E:\Downloads\fire_smoke_yolov8n.pt
```

The model is loaded only when analysis is requested, so application startup
does not depend on loading the checkpoint. The checkpoint must remain
available at the configured path for video analysis to complete.

The analysis outcome maps the model's frame predictions as follows:

| Result | Acceptance rule | Incident behavior |
| --- | --- | --- |
| Fire | At least three distinct prediction frames contain a `fire` detection with confidence of 50% or greater. | Creates a session-local Fire incident. |
| Smoke | At least one prediction frame contains a `smoke` detection with confidence of 50% or greater, when Fire does not qualify. | Creates a session-local Smoke incident. |
| No Detection | Neither Fire nor Smoke meets its acceptance rule. | Does not create an incident. |

When both outcomes qualify, Fire takes precedence. Positive results return the
highest qualifying confidence for the accepted outcome; No Detection has no
confidence value. If the checkpoint, YOLO runtime, or uploaded video cannot be
processed, the API returns an inference failure rather than creating an
incident.

A positive result creates an in-memory incident visible in the dashboard,
incident history, and events API, and increases the corresponding incident and
alert counts. No Detection and uploading alone never create incidents.
Positive results are deduplicated by the supplied filename, case-insensitively,
for the application session, even when separate uploads have different IDs.
The Video Testing UI submits the original filename returned by the upload
endpoint.

FastAPI parses multipart data before the application copies the uploaded file.
This local demo has no application-level file-size limit, total-session disk
quota, expiration timer, cloud storage, or database; restarting clears
generated videos and resets in-memory incidents.

## Mock Detection Provider

`MockDetectionProvider` remains the active provider for the standalone
monitoring baseline. It provides fixed in-memory data every time the
application starts:

- Four sample cameras, including active and offline source states.
- Five historical detection events: two Fire events and three Smoke events.
- A provider status named `Mock Detection Provider` with an operational, ready
  processing state.

This deterministic behavior keeps the initial dashboard state repeatable.
YOLO Video Testing results add session-local incidents without changing the
provider's fixed sample records or camera inventory; restarting restores the
initial counts.

## Baseline boundaries

This intentionally small baseline excludes databases, authentication, Docker,
cloud integrations, AWS services, audio or multimodal features, random
background event generation, and RTSP connections. It uses a deterministic
monitoring-data provider while providing real local YOLO inference for uploaded
video analysis.
