import { Link } from "react-router-dom"
import { ClipboardCheck } from "lucide-react"

import { AnalysisStatusBadge } from "@/components/status"
import type { ReviewSummary } from "@/lib/api"
import { formatDateTime } from "@/lib/format"

export function ReviewListItem({ review }: { review: ReviewSummary }) {
  const timestamp = review.completed_at ?? review.started_at
  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card p-4">
      <div className="min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Link
            to={`/pull-requests/${review.pull_request_id}`}
            className="truncate font-medium transition-colors hover:text-primary hover:underline"
          >
            {review.repository_full_name}
            <span className="text-muted-foreground"> #{review.pr_number}</span>{" "}
            {review.pr_title}
          </Link>
        </div>
        <p className="text-xs text-muted-foreground">
          {review.pr_author}
          {timestamp ? ` · ${formatDateTime(timestamp)}` : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <AnalysisStatusBadge status={review.status} />
        {review.merge_readiness_score != null ? (
          <span className="font-mono text-lg font-semibold">
            {review.merge_readiness_score}
            <span className="text-xs text-muted-foreground">/100</span>
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">No score</span>
        )}
      </div>
    </li>
  )
}