import type { ReactNode } from 'react'
import { api } from '../api/client'
import { PageHeading } from '../components/PageHeading'
import { ErrorBanner, Skeleton } from '../components/States'
import { Eyebrow, Panel, SectionTitle, StatusDot } from '../components/ui'
import { useApi } from '../hooks/useApi'

const REFRESH_MS = 15_000

function StatusCard({ eyebrow, title, children }: { eyebrow: string; title: ReactNode; children: ReactNode }) {
  return (
    <Panel>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h2 className="mb-4 text-lg font-bold">{title}</h2>
      <p className="flex items-center gap-2">{children}</p>
    </Panel>
  )
}

export function StatusPage() {
  const { data: status, error, reload } = useApi(api.getHealth, REFRESH_MS)

  return (
    <>
      <PageHeading
        documentTitle="System Status"
        eyebrow="Operational readiness"
        title="System Status"
        description="Current application and detection-provider availability."
      />

      {error && <ErrorBanner message={error} onRetry={reload} />}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatusCard eyebrow="Application" title={status ? status.application_status : <Skeleton width="w-28" />}>
          <StatusDot tone={status && !error ? 'active' : 'offline'} />
          {error ? 'VisionGuard backend is not reachable.' : 'VisionGuard web monitoring is available.'}
        </StatusCard>
        <StatusCard eyebrow="Detection Provider" title={status ? status.provider.name : <Skeleton width="w-36" />}>
          <StatusDot tone="active" />
          {status ? status.provider.status : '…'}
        </StatusCard>
        <StatusCard eyebrow="Processing" title="Ready">
          {status ? status.provider.processing_status : '…'}
        </StatusCard>
        <StatusCard
          eyebrow="Active Sources"
          title={status ? `${status.active_sources} / ${status.total_sources}` : <Skeleton width="w-14" />}
        >
          Configured YOLO camera sources currently active.
        </StatusCard>
      </section>

      <Panel className="mt-4">
        <Eyebrow>Integration boundary</Eyebrow>
        <SectionTitle>YOLO detection integration</SectionTitle>
        <p>
          The current <strong>YOLO Detection Provider</strong> supplies YOLO-based detection results. A future
          VisionAI Framework package can be wrapped in a provider adapter that returns the same source and event
          models, without changing these pages or APIs.
        </p>
      </Panel>
    </>
  )
}
