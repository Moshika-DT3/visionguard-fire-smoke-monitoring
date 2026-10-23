import type { CameraSource, DashboardMetrics, DetectionEvent } from './types'

/** Same calculation as MonitoringService.get_metrics in the backend. */
export function computeMetrics(cameras: CameraSource[], events: DetectionEvent[]): DashboardMetrics {
  return {
    active_cameras: cameras.filter((camera) => camera.status === 'active').length,
    total_incidents: events.length,
    fire_alerts: events.filter((event) => event.event_type === 'fire').length,
    smoke_alerts: events.filter((event) => event.event_type === 'smoke').length,
  }
}
