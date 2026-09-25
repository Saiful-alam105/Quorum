import { Link } from "react-router-dom"
import { GitPullRequestArrow } from "lucide-react"

import { SeverityDot } from "@/components/severity"
import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"
import type { PullRequestSummary } from "@/lib/api"
import { formatUpdatedAt } from "@/lib/format"

type SeverityRow = {
  label: string
  count: number
  dot: "critical" | "high" | "medium" | "low"
}

export function PullRequestReviewCard({
  pullRequest,
}: {
  pullRequest: PullRequestSummary
}) {
  const prUrl = pullRequest.repository_full_name
    ? `https://github.com/${pullRequest.repository_full_name}/pull/${pullRequest.number}`
    : null

  const rows: SeverityRow[] = [
    { label: "Critical", count: pullRequest.critical_count, dot: "critical" },
    { label: "High", count: pullRequest.high_count, dot: "high" },
    { label: "Medium", count: pullRequest.medium_count, dot: "medium" },
    { label: "Low", count: pullRequest.low_count, dot: "low" },
  ]
  const severityRows = rows.filter((row) => row.count > 0)

  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
            <GitPullRequestArrow className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <Link
              to={`/pull-requests/${pullRequest.id}`}
              className="block truncate font-medium transition-colors hover:text-primary hover:underline"
            >
              Pull Request{" "}
              <span className="text-muted-foreground">
                #{pullRequest.number}
              </span>
            </Link>
            <p className="truncate text-xs text-muted-foreground">
              {pullRequest.title}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <AnalysisStatusBadge status={pullRequest.latest_analysis_status} />
          <PrStateBadge state={pullRequest.state} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Security</p>
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
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Tests</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {pullRequest.test_count > 0
              ? `${pullRequest.test_count} generated`
              : "No tests generated"}
          </p>
        </div>
        <div className="rounded-lg border border-border p-4">
          <p className="text-xs text-muted-foreground">Merge Readiness</p>
          {pullRequest.merge_readiness_score != null ? (
            <p className="mt-2 font-mono text-2xl font-semibold">
              {pullRequest.merge_readiness_score}
              <span className="text-xs text-muted-foreground">/100</span>
            </p>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">No score yet</p>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-border pt-3 text-xs text-muted-foreground">
        <span>{pullRequest.repository_full_name ?? "unknown/repo"}</span>
        <span>· Author: {pullRequest.author}</span>
        {pullRequest.updated_at ? (
          <span>· {formatUpdatedAt(pullRequest.updated_at)}</span>
        ) : null}
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