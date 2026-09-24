import { Link } from "react-router-dom"

import { SeverityBadge } from "@/components/severity"
import type { Finding } from "@/lib/api"

export function FindingListItem({ finding }: { finding: Finding }) {
  return (
    <li className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card p-4">
      <div className="min-w-0 space-y-1.5">
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className="truncate text-sm font-medium">{finding.title}</span>
        </div>
        <p className="truncate font-mono text-xs text-muted-foreground">
          {finding.file}
          {finding.line != null ? `:${finding.line}` : ""}
        </p>
        <Link
          to={`/pull-requests/${finding.pull_request_id}`}
          className="block truncate text-xs text-muted-foreground transition-colors hover:text-primary"
        >
          {finding.repository_full_name} #{finding.pr_number} · {finding.pr_title}
        </Link>
      </div>
    </li>
  )
}