import { useEffect, type ReactNode } from 'react'
import { Eyebrow } from './ui'

interface PageHeadingProps {
  eyebrow: string
  title: string
  description: string
  /** Browser tab title suffix, e.g. "Dashboard" -> "VisionGuard | Dashboard" */
  documentTitle: string
  aside?: ReactNode
}

export function PageHeading({ eyebrow, title, description, documentTitle, aside }: PageHeadingProps) {
  useEffect(() => {
    document.title = `VisionGuard | ${documentTitle}`
  }, [documentTitle])

  return (
    <section className="mb-6 flex flex-col items-start justify-between gap-4 sm:flex-row">
      <div>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h1 className="mb-1 text-[clamp(1.8rem,4vw,2.5rem)] leading-tight font-bold">{title}</h1>
        <p className="text-muted">{description}</p>
      </div>
      {aside}
    </section>
  )
}
