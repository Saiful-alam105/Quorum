import { Link } from "react-router-dom"
import { Compass } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="space-y-4 text-center">
        <EmptyState
          icon={Compass}
          title="Page not found"
          description="The page you are looking for does not exist in the Quorum dashboard."
        />
        <Link
          to="/"
          className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}
