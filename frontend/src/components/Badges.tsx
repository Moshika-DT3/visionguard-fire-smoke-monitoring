import type { ReactNode } from 'react'
import type { CameraStatus, EventType, Severity, VideoAnalysisOutcome } from '../api/types'
import { titleCase } from '../utils/format'
import { cx } from './styles'
import { StatusDot } from './ui'

const pill = 'inline-block rounded-full px-2.5 py-1 text-xs font-extrabold'

const OUTCOME_STYLES: Record<VideoAnalysisOutcome, string> = {
  fire: 'bg-[#fde4df] text-[#9e2c22]',
  smoke: 'bg-[#eee5fc] text-[#6841a0]',
  no_detection: 'bg-[#e8f7f0] text-[#126b4a]',
}

const SEVERITY_STYLES: Record<Severity, string> = {
  low: 'bg-[#e8f0fb] text-[#36608f]',
  medium: 'bg-[#fff1da] text-[#9a5b06]',
  high: 'bg-[#fde7d7] text-[#a84410]',
  critical: 'bg-[#fde1e1] text-[#a32424]',
}

export function EventTypeBadge({ type }: { type: EventType }) {
  return <span className={cx(pill, OUTCOME_STYLES[type])}>{titleCase(type)}</span>
}

export function OutcomeBadge({ outcome, label }: { outcome: VideoAnalysisOutcome; label: string }) {
  return <span className={cx(pill, OUTCOME_STYLES[outcome])}>{label}</span>
}

export function SeverityBadge({ severity, label }: { severity: Severity; label?: string }) {
  return <span className={cx(pill, SEVERITY_STYLES[severity])}>{label ?? titleCase(severity)}</span>
}

const chip = 'inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-bold'

export function SourceStatus({ status }: { status: CameraStatus }) {
  return (
    <span className={cx(chip, status === 'active' ? 'bg-[#e8f7f0] text-[#126b4a]' : 'bg-[#fdf0f0] text-danger')}>
      <StatusDot tone={status} />
      {titleCase(status)}
    </span>
  )
}

export function OperationalChip({ children }: { children: ReactNode }) {
  return (
    <div className={cx(chip, 'shrink-0 bg-[#e8f7f0] text-[#126b4a]')}>
      <StatusDot tone="active" />
      {children}
    </div>
  )
}
