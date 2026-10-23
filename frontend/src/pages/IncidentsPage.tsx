import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { api } from '../api/client'
import { EventTypeBadge, SeverityBadge } from '../components/Badges'
import { PageHeading } from '../components/PageHeading'
import { ErrorBanner, TableMessageRow } from '../components/States'
import { cx } from '../components/styles'
import { Panel, Subtext, TBody, Table, Td, Th } from '../components/ui'
import { useApi } from '../hooks/useApi'
import { formatDetectedAt, formatPercent } from '../utils/format'

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'fire', label: 'Fire' },
  { value: 'smoke', label: 'Smoke' },
] as const

type Filter = (typeof FILTERS)[number]['value']

/** Same normalization as the server-rendered /incidents page: unknown values fall back to "all". */
function normalizeFilter(raw: string | null): Filter {
  const value = (raw ?? 'all').toLowerCase()
  return value === 'fire' || value === 'smoke' ? value : 'all'
}

const REFRESH_MS = 15_000

export function IncidentsPage() {
  const [searchParams] = useSearchParams()
  const selected = normalizeFilter(searchParams.get('type'))
  const { data: events, error, reload } = useApi(api.getEvents, REFRESH_MS)

  // GET /api/events has no filter parameter, so filter client-side.
  const visibleEvents = useMemo(
    () => (selected === 'all' ? events : events?.filter((event) => event.event_type === selected)),
    [events, selected],
  )

  return (
    <>
      <PageHeading
        documentTitle="Incident History"
        eyebrow="Detection records"
        title="Incident History"
        description="Review YOLO-detected fire and smoke events captured by VisionGuard."
      />

      <nav aria-label="Incident type filters" className="mb-4 flex gap-2">
        {FILTERS.map((filter) => {
          const isActive = selected === filter.value
          const count = events
            ? filter.value === 'all'
              ? events.length
              : events.filter((event) => event.event_type === filter.value).length
            : null
          return (
            <Link
              key={filter.value}
              to={`/incidents?type=${filter.value}`}
              aria-current={isActive ? 'page' : undefined}
              className={cx(
                'inline-flex items-center rounded-lg border px-3.5 py-2 font-bold no-underline transition-colors',
                isActive
                  ? 'border-brand bg-brand text-white'
                  : 'border-line text-muted hover:border-brand hover:text-brand',
              )}
            >
              {filter.label}
              {count !== null && (
                <span
                  className={cx(
                    'ml-2 rounded-full px-1.5 text-xs',
                    isActive ? 'bg-white/25 text-white' : 'bg-line text-ink',
                  )}
                >
                  {count}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {error && <ErrorBanner message={error} onRetry={reload} />}

      <Panel>
        <Table caption="Filtered detection event history">
          <thead>
            <tr>
              <Th>Event</Th>
              <Th>Detection Type</Th>
              <Th>Camera / Source</Th>
              <Th>Confidence</Th>
              <Th>Severity</Th>
              <Th>Handling Status</Th>
            </tr>
          </thead>
          <TBody>
            {!events && !error && <TableMessageRow colSpan={6}>Loading detection events…</TableMessageRow>}
            {visibleEvents?.length === 0 && (
              <TableMessageRow colSpan={6}>No matching detection events are available.</TableMessageRow>
            )}
            {visibleEvents?.map((event) => (
              <tr key={event.id}>
                <Td>
                  <strong>{event.id}</strong>
                  <Subtext>{formatDetectedAt(event.detected_at)}</Subtext>
                </Td>
                <Td>
                  <EventTypeBadge type={event.event_type} />
                </Td>
                <Td>
                  {event.camera_name}
                  <Subtext>{event.camera_id}</Subtext>
                </Td>
                <Td>{formatPercent(event.confidence)}</Td>
                <Td>
                  <SeverityBadge severity={event.severity} />
                </Td>
                <Td>{event.status}</Td>
              </tr>
            ))}
          </TBody>
        </Table>
      </Panel>
    </>
  )
}
