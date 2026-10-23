import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { api } from '../api/client'
import { computeMetrics } from '../api/metrics'
import { EventTypeBadge, OperationalChip, SeverityBadge } from '../components/Badges'
import { PageHeading } from '../components/PageHeading'
import { ErrorBanner, Skeleton, TableMessageRow } from '../components/States'
import {
  DetailList,
  DetailRow,
  Eyebrow,
  Panel,
  SectionTitle,
  StatusDot,
  Subtext,
  TBody,
  Table,
  Td,
  Th,
} from '../components/ui'
import { buttonClass, cx, textLinkClass } from '../components/styles'
import { useApi } from '../hooks/useApi'
import { formatDetectedAt, formatPercent } from '../utils/format'

const RECENT_EVENT_LIMIT = 4
const REFRESH_MS = 15_000

async function loadDashboard(signal: AbortSignal) {
  const [status, cameras, events] = await Promise.all([
    api.getHealth(signal),
    api.getCameras(signal),
    api.getEvents(signal),
  ])
  return {
    status,
    metrics: computeMetrics(cameras, events),
    recentEvents: events.slice(0, RECENT_EVENT_LIMIT),
  }
}

interface MetricCardProps {
  label: string
  value: number | undefined
  note: string
  accent: 'brand' | 'fire' | 'smoke'
}

const ACCENTS: Record<MetricCardProps['accent'], string> = {
  brand: 'border-t-brand',
  fire: 'border-t-fire',
  smoke: 'border-t-smoke',
}

function MetricCard({ label, value, note, accent }: MetricCardProps) {
  return (
    <Panel className={cx('border-t-4 p-[1.1rem]', ACCENTS[accent])}>
      <span className="block text-[0.82rem] font-bold text-muted">{label}</span>
      <strong className="my-1 block text-[2rem] leading-tight">{value ?? <Skeleton />}</strong>
      <small className="text-[0.8rem] text-muted">{note}</small>
    </Panel>
  )
}

function Loadable({ value, width }: { value: ReactNode | undefined; width: string }) {
  return <>{value ?? <Skeleton width={width} />}</>
}

export function DashboardPage() {
  const { data, error, reload } = useApi(loadDashboard, REFRESH_MS)
  const status = data?.status
  const metrics = data?.metrics

  return (
    <>
      <PageHeading
        documentTitle="Dashboard"
        eyebrow="Live monitoring overview"
        title="VisionGuard"
        description="Fire & smoke detection visibility across monitored sources."
        aside={status && <OperationalChip>{status.application_status}</OperationalChip>}
      />

      {error && <ErrorBanner message={error} onRetry={reload} />}

      <section aria-label="Monitoring summary" className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Active Cameras"
          value={metrics?.active_cameras}
          note={status ? `${status.total_sources} configured sources` : 'Loading sources…'}
          accent="brand"
        />
        <MetricCard
          label="Total Incidents"
          value={metrics?.total_incidents}
          note="YOLO detection event history"
          accent="brand"
        />
        <MetricCard label="Fire Alerts" value={metrics?.fire_alerts} note="Requires immediate attention" accent="fire" />
        <MetricCard
          label="Smoke Alerts"
          value={metrics?.smoke_alerts}
          note="Review monitoring conditions"
          accent="smoke"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,0.85fr)]">
        <Panel>
          <div className="flex items-start justify-between gap-4">
            <div>
              <Eyebrow>Detection activity</Eyebrow>
              <SectionTitle>Recent Detection Events</SectionTitle>
            </div>
            <Link className={textLinkClass} to="/incidents">
              View all incidents
            </Link>
          </div>
          <Table caption="Recent fire and smoke detection events">
            <thead>
              <tr>
                <Th>Event</Th>
                <Th>Type</Th>
                <Th>Source</Th>
                <Th>Confidence</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <TBody>
              {!data && !error && <TableMessageRow colSpan={5}>Loading detection events…</TableMessageRow>}
              {data?.recentEvents.length === 0 && (
                <TableMessageRow colSpan={5}>No detection events recorded yet.</TableMessageRow>
              )}
              {data?.recentEvents.map((event) => (
                <tr key={event.id}>
                  <Td>
                    <strong>{event.id}</strong>
                    <Subtext>{formatDetectedAt(event.detected_at)}</Subtext>
                  </Td>
                  <Td>
                    <EventTypeBadge type={event.event_type} />
                  </Td>
                  <Td>{event.camera_name}</Td>
                  <Td>{formatPercent(event.confidence)}</Td>
                  <Td>
                    <SeverityBadge severity={event.severity} label={event.status} />
                  </Td>
                </tr>
              ))}
            </TBody>
          </Table>
        </Panel>

        <Panel>
          <Eyebrow>System health</Eyebrow>
          <SectionTitle>Monitoring Status</SectionTitle>
          <DetailList>
            <DetailRow label="Application">
              {status ? (
                <>
                  <StatusDot tone="active" />
                  {status.application_status}
                </>
              ) : (
                <Skeleton width="w-20" />
              )}
            </DetailRow>
            <DetailRow label="Provider">
              <Loadable value={status?.provider.name} width="w-28" />
            </DetailRow>
            <DetailRow label="Provider status">
              <Loadable value={status?.provider.status} width="w-20" />
            </DetailRow>
            <DetailRow label="Processing">
              <Loadable value={status?.provider.processing_status} width="w-24" />
            </DetailRow>
            <DetailRow label="Active sources">
              <Loadable value={status && `${status.active_sources} of ${status.total_sources}`} width="w-14" />
            </DetailRow>
          </DetailList>
          <Link className={cx(buttonClass, 'mt-4 w-full')} to="/status">
            View system status
          </Link>
        </Panel>
      </section>
    </>
  )
}
