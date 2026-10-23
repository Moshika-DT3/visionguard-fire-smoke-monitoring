import type {
  CameraSource,
  DetectionEvent,
  MonitoringStatus,
  VideoAnalysisResult,
  VideoUploadResponse,
} from './types'

/**
 * Base URL for the FastAPI backend. Empty by default so requests go to the
 * same origin (the Vite dev proxy forwards /api to the backend).
 */
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** FastAPI errors use { detail: string } or, for validation, { detail: [{ msg }] }. */
function extractDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null
  const { detail } = body as { detail: unknown }
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : null))
      .filter(Boolean)
    return messages.length ? messages.join('; ') : null
  }
  return null
}

async function request<T>(path: string, init: RequestInit = {}, fallbackError = 'Request failed.'): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new ApiError(0, 'Unable to reach the VisionGuard server. Check that the backend is running.')
  }

  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, extractDetail(body) ?? fallbackError)
  }
  return body as T
}

/** Build an absolute URL for a backend path such as an upload's preview_url. */
export function resolveApiUrl(path: string): string {
  return `${API_BASE}${path}`
}

export const api = {
  /** GET /api/health */
  getHealth: (signal?: AbortSignal) =>
    request<MonitoringStatus>('/api/health', { signal }, 'Could not load system status.'),

  /** GET /api/cameras */
  getCameras: (signal?: AbortSignal) =>
    request<CameraSource[]>('/api/cameras', { signal }, 'Could not load camera sources.'),

  /** GET /api/events (newest first) */
  getEvents: (signal?: AbortSignal) =>
    request<DetectionEvent[]>('/api/events', { signal }, 'Could not load detection events.'),

  /** POST /api/video-tests/upload (multipart, field "file") */
  uploadVideo: (file: File) => {
    const payload = new FormData()
    payload.append('file', file)
    return request<VideoUploadResponse>(
      '/api/video-tests/upload',
      { method: 'POST', body: payload },
      'The video could not be uploaded.',
    )
  },

  /** POST /api/video-tests/{video_id}/analyze?filename=... */
  analyzeVideo: (videoId: string, filename: string) =>
    request<VideoAnalysisResult>(
      `/api/video-tests/${encodeURIComponent(videoId)}/analyze?filename=${encodeURIComponent(filename)}`,
      { method: 'POST' },
      'Analysis could not be completed.',
    ),

  /** GET /api/video-tests/uploads/{video_id}, used as a <video> src. */
  videoPreviewUrl: (videoId: string) => resolveApiUrl(`/api/video-tests/uploads/${encodeURIComponent(videoId)}`),
}
