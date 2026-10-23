import { Link } from 'react-router'
import { PageHeading } from '../components/PageHeading'
import { buttonClass } from '../components/styles'

export function NotFoundPage() {
  return (
    <>
      <PageHeading
        documentTitle="Not Found"
        eyebrow="404"
        title="Page not found"
        description="The page you are looking for does not exist."
      />
      <Link className={buttonClass} to="/">
        Back to dashboard
      </Link>
    </>
  )
}
