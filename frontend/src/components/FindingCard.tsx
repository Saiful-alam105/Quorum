import { Link } from "react-router-dom"

import { normalizeSeverity, SeverityBadge, severityConfig } from "@/components/severity"
import type { Finding } from "@/lib/api"
import { cn } from "@/lib/utils"

export function FindingCard({ finding }: { finding: Finding }) {
  const config = severityConfig[normalizeSeverity(finding.severity)]

  return (
    <li
      className={cn(
        "rounded-lg border border-border border-l-2 bg-card p-4",
        config.borderClass,
      )}
    >
      <div className="min-w-0 space-y-1.5">
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className="truncate text-sm font-medium">{finding.title}</span>
        </div>
        <p className="truncate font-mono text-xs text-muted-foreground">
          {finding.file}
          {finding.line != null ? `:${finding.line}` : ""}
          {finding.rule_id ? ` · ${finding.rule_id}` : ""}
        </p>
        {finding.evidence ? (
          <p className="line-clamp-2 text-xs text-muted-foreground">
            {finding.evidence}
          </p>
        ) : null}
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