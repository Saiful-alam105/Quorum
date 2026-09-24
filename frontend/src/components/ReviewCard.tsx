import { Link } from "react-router-dom"
import { ClipboardCheck } from "lucide-react"

import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"
import type { ReviewSummary } from "@/lib/api"
import { formatDateTime } from "@/lib/format"

export function ReviewCard({ review }: { review: ReviewSummary }) {
  const prUrl = review.repository_full_name
    ? `https://github.com/${review.repository_full_name}/pull/${review.pr_number}`
    : null
  const timestamp = review.completed_at ?? review.started_at

  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
            <ClipboardCheck className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <Link
              to={`/reviews/${review.id}`}
              className="block truncate font-medium transition-colors hover:text-primary hover:underline"
            >
              Pull Request{" "}
              <span className="text-muted-foreground">#{review.pr_number}</span>
            </Link>
            <p className="truncate text-xs text-muted-foreground">
              {review.pr_title}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <AnalysisStatusBadge status={review.status} />
          <PrStateBadge state={review.pr_state} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Merge Readiness</p>
          {review.merge_readiness_score != null ? (
            <>
              <p className="mt-2 font-mono text-2xl font-semibold">
                {review.merge_readiness_score}
                <span className="text-xs text-muted-foreground">/100</span>
              </p>
              {review.recommendation ? (
                <p className="mt-1 text-xs font-medium text-success">
                  {review.recommendation}
                </p>
              ) : null}
            </>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">No score yet</p>
          )}
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Security</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {review.finding_count > 0
              ? `${review.finding_count} ${
                  review.finding_count === 1 ? "finding" : "findings"
                }`
              : "No findings"}
          </p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Tests</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {review.test_count > 0
              ? `${review.test_count} generated`
              : "No tests generated"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-border pt-3 text-xs text-muted-foreground">
        <span>{review.repository_full_name}</span>
        <span>· Author: {review.pr_author}</span>
        {timestamp ? <span>· {formatDateTime(timestamp)}</span> : null}
        {prUrl ? (
          <a
            href={prUrl}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            GitHub ↗
          </a>
        ) : null}
      </div>
    </li>
  )
}