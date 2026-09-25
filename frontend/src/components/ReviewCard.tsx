import { Link } from "react-router-dom"
import { ClipboardCheck } from "lucide-react"

import { SeverityDot } from "@/components/severity"
import { AnalysisStatusBadge } from "@/components/status"
import type { ReviewSummary } from "@/lib/api"
import { formatDateTime } from "@/lib/format"

type SeverityRow = {
  label: string
  count: number
  dot: "critical" | "high" | "medium" | "low"
}

export function ReviewCard({ review }: { review: ReviewSummary }) {
  const prUrl = review.repository_full_name
    ? `https://github.com/${review.repository_full_name}/pull/${review.pr_number}`
    : null
  const timestamp = review.completed_at ?? review.started_at

  const rows: SeverityRow[] = [
    { label: "Critical", count: review.critical_count, dot: "critical" },
    { label: "High", count: review.high_count, dot: "high" },
    { label: "Medium", count: review.medium_count, dot: "medium" },
    { label: "Low", count: review.low_count, dot: "low" },
  ]
  const severityRows = rows.filter((row) => row.count > 0)

  return (
    <li className="rounded-xl border border-border bg-card p-6 shadow-lg">
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
        <div className="flex items-center gap-3">
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
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Security findings</p>
          {severityRows.length === 0 ? (
            <p className="mt-2 text-sm text-muted-foreground">No findings</p>
          ) : (
            <ul className="mt-2 space-y-1.5 text-sm">
              {severityRows.map((row) => (
                <li key={row.label} className="flex items-center gap-2">
                  <SeverityDot severity={row.dot} />
                  <span className="text-muted-foreground">
                    {row.count} {row.label.toLowerCase()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="space-y-4">
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Tests</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {review.test_count > 0
                ? `${review.test_count} generated`
                : "No tests generated"}
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Coverage</p>
            {review.coverage_after != null ? (
              <p className="mt-1 font-mono text-sm">
                {review.coverage_before != null
                  ? `${review.coverage_before.toFixed(0)}%`
                  : "—"}{" "}
                <span className="text-muted-foreground">→</span>{" "}
                {review.coverage_after.toFixed(0)}%
                {review.coverage_delta != null ? (
                  <span className="ml-1 text-success">
                    {review.coverage_delta >= 0 ? "+" : ""}
                    {review.coverage_delta.toFixed(0)}%
                  </span>
                ) : null}
              </p>
            ) : (
              <p className="mt-1 text-sm text-muted-foreground">Not measured</p>
            )}
          </div>
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