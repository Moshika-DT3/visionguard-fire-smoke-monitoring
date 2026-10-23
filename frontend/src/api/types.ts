// TypeScript mirrors of the Pydantic models in backend/models.py.

export type CameraStatus = 'active' | 'offline'
export type EventType = 'fire' | 'smoke'
export type Severity = 'low' | 'medium' | 'high' | 'critical'
export type VideoAnalysisOutcome = 'fire' | 'smoke' | 'no_detection'

export interface CameraSource {
  id: string
  name: string
  location: string
  status: CameraStatus
  source_type: string
}

export interface DetectionEvent {
  id: string
  event_type: EventType
  camera_id: string
  camera_name: string
  /** 0 to 1 */
  confidence: number
  /** ISO-8601 timestamp */
  detected_at: string
  severity: Severity
  status: string
}

export interface ProviderStatus {
  name: string
  status: string
  processing_status: string
}

export interface MonitoringStatus {
  application_status: string
  provider: ProviderStatus
  active_sources: number
  total_sources: number
}

/** Computed client-side; the backend has no metrics endpoint. */
export interface DashboardMetrics {
  active_cameras: number
  total_incidents: number
  fire_alerts: number
  smoke_alerts: number
}

/** Response of POST /api/video-tests/upload */
export interface VideoUploadResponse {
  video_id: string
  filename: string
  preview_url: string
}

/** Response of POST /api/video-tests/{video_id}/analyze */
export interface VideoAnalysisResult {
  filename: string
  outcome: VideoAnalysisOutcome
  confidence: number | null
  status: string
  provider: string
  incident_created: boolean
}
