import { useState, type ChangeEvent, type DragEvent, type FormEvent } from 'react'
import { Link } from 'react-router'
import { api, resolveApiUrl } from '../api/client'
import type { VideoAnalysisOutcome, VideoAnalysisResult, VideoUploadResponse } from '../api/types'
import { OperationalChip, OutcomeBadge } from '../components/Badges'
import { PageHeading } from '../components/PageHeading'
import { Spinner } from '../components/States'
import { buttonClass, cx, textLinkClass } from '../components/styles'
import { DetailList, DetailRow, Eyebrow, Panel, SectionTitle } from '../components/ui'
import { formatPercent } from '../utils/format'

const OUTCOME_LABELS: Record<VideoAnalysisOutcome, string> = {
  fire: 'Fire',
  smoke: 'Smoke',
  no_detection: 'No Detection',
}

const OUTCOME_NOTES: Record<VideoAnalysisOutcome, string> = {
  fire: 'Model inference completed. Fire was detected in at least three qualifying video frames. An incident was created or already exists for this video.',
  smoke:
    'Model inference completed. Smoke was detected in at least one qualifying video frame. An incident was created or already exists for this video.',
  no_detection:
    'Model inference completed. No Fire or Smoke detection met the acceptance threshold, so no incident was created.',
}

type Busy = 'idle' | 'uploading' | 'analyzing'

function incidentFlowText(result: VideoAnalysisResult): string {
  if (result.incident_created) return 'Created and visible in Dashboard / Incident History'
  return result.outcome === 'no_detection' ? 'No incident created' : 'Already created for this video this session'
}

export function VideoTestingPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null)
  const [result, setResult] = useState<VideoAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<Busy>('idle')
  const [dragActive, setDragActive] = useState(false)

  const isBusy = busy !== 'idle'

  const selectFile = (file: File | null) => {
    setSelectedFile(file)
    setError(null)
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.target.files?.[0] ?? null)
  }

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setDragActive(false)
    if (isBusy) return
    const file = event.dataTransfer.files?.[0]
    if (file) selectFile(file)
  }

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedFile) {
      setError('Please select an MP4 video file.')
      return
    }
    if (!selectedFile.name.toLowerCase().endsWith('.mp4')) {
      setError('Only MP4 video files are supported.')
      return
    }

    setError(null)
    setBusy('uploading')
    try {
      const uploaded = await api.uploadVideo(selectedFile)
      setUploadedVideo(uploaded)
      setResult(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The video could not be uploaded.')
    } finally {
      setBusy('idle')
    }
  }

  const handleAnalyze = async () => {
    if (!uploadedVideo) {
      setError('Upload an MP4 video before running analysis.')
      return
    }
    setError(null)
    setBusy('analyzing')
    try {
      setResult(await api.analyzeVideo(uploadedVideo.video_id, uploadedVideo.filename))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis could not be completed.')
    } finally {
      setBusy('idle')
    }
  }

  const isPositive = result ? result.outcome !== 'no_detection' : false

  return (
    <>
      <PageHeading
        documentTitle="Video Testing"
        eyebrow="Workflow validation"
        title="Video Testing"
        description="Upload an MP4 to preview and run real video analysis using YOLO."
        aside={<OperationalChip>YOLO workflow ready</OperationalChip>}
      />

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.8fr)]">
        <Panel>
          <Eyebrow>Step 1</Eyebrow>
          <SectionTitle>Upload &amp; Preview</SectionTitle>

          <form className="grid gap-3.5" noValidate onSubmit={handleUpload}>
            <label
              htmlFor="video-file"
              onDragOver={(event) => {
                event.preventDefault()
                if (!isBusy) setDragActive(true)
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              className={cx(
                'grid cursor-pointer justify-items-center gap-1.5 rounded-xl border-2 border-dashed px-4 py-8 text-center text-muted transition-colors',
                'hover:border-brand hover:bg-[#f1f7ff] focus-within:border-brand focus-within:bg-[#f1f7ff]',
                dragActive ? 'border-brand bg-[#e7f1ff]' : 'border-[#b8c9e1] bg-[#f8fbff]',
              )}
            >
              <span
                aria-hidden="true"
                className="grid size-9 place-items-center rounded-full bg-[#dbeafa] text-xl font-extrabold text-brand"
              >
                ↑
              </span>
              <strong className="text-ink">Select or drop an MP4 video</strong>
              <span>Demo files remain local to this application session.</span>
              <input
                id="video-file"
                name="file"
                type="file"
                accept="video/mp4,.mp4"
                required
                disabled={isBusy}
                onChange={handleFileChange}
                className="max-w-full text-sm file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-[#dbeafa] file:px-3 file:py-1.5 file:font-bold file:text-brand disabled:opacity-60"
              />
            </label>

            {error && (
              <p role="alert" className="font-bold text-danger">
                {error}
              </p>
            )}
            <p aria-live="polite" className="min-h-6 text-[0.9rem] text-muted wrap-anywhere">
              {selectedFile ? `Selected: ${selectedFile.name}` : 'No file selected.'}
            </p>
            <button className={cx(buttonClass, 'justify-self-start')} type="submit" disabled={isBusy}>
              {busy === 'uploading' ? 'Uploading…' : 'Upload video'}
            </button>
          </form>

          {uploadedVideo && (
            <div className="mt-6 border-t border-line pt-5">
              <Eyebrow>Uploaded preview</Eyebrow>
              <video
                key={uploadedVideo.video_id}
                controls
                preload="metadata"
                src={resolveApiUrl(uploadedVideo.preview_url)}
                className="my-3 block max-h-90 w-full rounded-[10px] bg-navy"
              >
                Your browser does not support MP4 video preview.
              </video>
              <p className="mb-4 text-muted">Uploaded filename: {uploadedVideo.filename}</p>
              <button className={buttonClass} type="button" disabled={isBusy} onClick={handleAnalyze}>
                {busy === 'analyzing' ? 'Analyzing…' : 'Run Analysis'}
              </button>
            </div>
          )}
        </Panel>

        <Panel aria-live="polite" aria-busy={busy === 'analyzing'} className="min-h-65">
          <Eyebrow>Step 2</Eyebrow>
          <SectionTitle>Analysis Result</SectionTitle>

          {busy === 'analyzing' && (
            <div className="text-muted">
              <p className="mb-2">
                <Spinner />
                Running YOLO inference on the uploaded video…
              </p>
              <small className="text-[0.8rem]">This can take a while for longer videos.</small>
            </div>
          )}

          {busy !== 'analyzing' && !result && (
            <div className="text-muted">
              <p className="mb-2">Upload an MP4 and run analysis to see the YOLO detection result.</p>
              <small className="text-[0.8rem]">Provider: YOLO Video Analysis</small>
            </div>
          )}

          {busy !== 'analyzing' && result && (
            <div>
              <OutcomeBadge outcome={result.outcome} label={OUTCOME_LABELS[result.outcome]} />
              <DetailList className="my-4">
                <DetailRow label="Video">{result.filename}</DetailRow>
                <DetailRow label="Outcome">{OUTCOME_LABELS[result.outcome]}</DetailRow>
                {result.confidence !== null && (
                  <DetailRow label="Detection confidence">{formatPercent(result.confidence)}</DetailRow>
                )}
                <DetailRow label="Analysis status">{result.status}</DetailRow>
                <DetailRow label="Provider">{result.provider}</DetailRow>
                <DetailRow label="Incident flow">{incidentFlowText(result)}</DetailRow>
              </DetailList>
              <p className={cx('mb-3 text-[0.9rem] font-bold', isPositive ? 'text-fire' : 'text-ok')}>
                {OUTCOME_NOTES[result.outcome]}
              </p>
              {isPositive && (
                <Link className={textLinkClass} to={`/incidents?type=${result.outcome}`}>
                  View in Incident History →
                </Link>
              )}
            </div>
          )}
        </Panel>
      </section>
    </>
  )
}
