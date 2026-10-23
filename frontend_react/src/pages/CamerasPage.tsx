import { api } from '../api/client'
import { SourceStatus } from '../components/Badges'
import { PageHeading } from '../components/PageHeading'
import { ErrorBanner, TableMessageRow } from '../components/States'
import { Panel, TBody, Table, Td, Th } from '../components/ui'
import { useApi } from '../hooks/useApi'

export function CamerasPage() {
  const { data: cameras, error, reload } = useApi(api.getCameras)

  return (
    <>
      <PageHeading
        documentTitle="Camera Sources"
        eyebrow="Source inventory"
        title="Camera Sources"
        description="Sample sources modelled for a future RTSP or video integration."
      />

      {error && <ErrorBanner message={error} onRetry={reload} />}

      <Panel>
        <Table caption="Configured VisionGuard camera sources">
          <thead>
            <tr>
              <Th>Camera</Th>
              <Th>Identifier</Th>
              <Th>Location</Th>
              <Th>Source Type</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <TBody>
            {!cameras && !error && <TableMessageRow colSpan={5}>Loading camera sources…</TableMessageRow>}
            {cameras?.length === 0 && <TableMessageRow colSpan={5}>No camera sources are configured.</TableMessageRow>}
            {cameras?.map((camera) => (
              <tr key={camera.id}>
                <Td>
                  <strong>{camera.name}</strong>
                </Td>
                <Td>
                  <code className="font-mono font-bold text-[#334e7b]">{camera.id}</code>
                </Td>
                <Td>{camera.location}</Td>
                <Td>{camera.source_type}</Td>
                <Td>
                  <SourceStatus status={camera.status} />
                </Td>
              </tr>
            ))}
          </TBody>
        </Table>
      </Panel>
    </>
  )
}
