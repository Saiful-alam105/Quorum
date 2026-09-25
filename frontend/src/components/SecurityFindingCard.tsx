import { SeverityBadge } from "@/components/severity"
import type { SecurityFinding } from "@/lib/api"

export function SecurityFindingCard({
  finding,
}: {
  finding: SecurityFinding
}) {
  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-4">
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
        </div>
      </div>
      {finding.evidence ? (
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-md border border-border bg-background p-3 text-xs text-muted-foreground">
          {finding.evidence}
        </pre>
      ) : null}
      {finding.explanation ? (
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          {finding.explanation}
        </p>
      ) : null}
    </li>
  )
}