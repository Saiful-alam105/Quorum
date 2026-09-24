import { Link } from "react-router-dom"
import { GitPullRequest } from "lucide-react"

import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"
import type { PullRequestSummary } from "@/lib/api"
import { formatUpdatedAt } from "@/lib/format"

export function PullRequestListItem({
  pullRequest,
}: {
  pullRequest: PullRequestSummary
}) {
  const prUrl = pullRequest.repository_full_name
    ? `https://github.com/${pullRequest.repository_full_name}/pull/${pullRequest.number}`
    : null

  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card p-4">
      <div className="min-w-0 space-y-1.5">
        <div className="flex items-center gap-2">
          <GitPullRequest className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Link
            to={`/pull-requests/${pullRequest.id}`}
            className="truncate font-medium transition-colors hover:text-primary hover:underline"
          >
            {pullRequest.repository_full_name ?? "unknown/repo"}
            <span className="text-muted-foreground">
              {" "}
              #{pullRequest.number}
            </span>{" "}
            {pullRequest.title}
          </Link>
        </div>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span>Author: {pullRequest.author}</span>
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
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {pullRequest.finding_count > 0 ? (
          <span
            className={
              pullRequest.critical_count > 0
                ? "text-xs font-medium text-severity-critical"
                : "text-xs text-muted-foreground"
            }
          >
            {pullRequest.finding_count}{" "}
            {pullRequest.finding_count === 1 ? "finding" : "findings"}
          </span>
        ) : null}
        <AnalysisStatusBadge status={pullRequest.latest_analysis_status} />
        <PrStateBadge state={pullRequest.state} />
      </div>
    </li>
  )
}