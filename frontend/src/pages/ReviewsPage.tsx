import { ClipboardCheck } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function ReviewsPage() {
  return (
    <>
      <PageHeader
        title="Reviews"
        description="Quorum analysis results and Merge Readiness Scores."
      />
      <EmptyState
        icon={ClipboardCheck}
        title="No reviews to show yet"
        description="Reviews, security findings, generated tests, and coverage will appear here once the analysis pipeline is implemented. No analysis data exists yet."
      />
    </>
  )
}
