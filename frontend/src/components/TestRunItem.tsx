import { Badge } from "@/components/ui/Badge"
import type { TestRun } from "@/lib/api"

type BadgeVariant = "success" | "danger" | "muted" | "secondary"

function statusVariant(status: string): BadgeVariant {
  const normalized = status.toLowerCase()
  if (normalized === "passed") {
    return "success"
  }
  if (normalized === "failed" || normalized === "error") {
    return "danger"
  }
  if (normalized === "skipped") {
    return "muted"
  }
  return "secondary"
}

export function TestRunItem({ test }: { test: TestRun }) {
  return (
    <li className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-4">
        <span className="truncate font-mono text-sm">{test.test_name}</span>
        <Badge variant={statusVariant(test.status)} className="capitalize">
          {test.status}
        </Badge>
      </div>
      {test.duration != null ? (
        <p className="mt-1.5 text-xs text-muted-foreground">
          Duration: {test.duration.toFixed(2)}s
        </p>
      ) : null}
      {test.failure_reason ? (
        <p className="mt-2 rounded-md border border-border bg-background p-2 text-xs text-severity-high">
          {test.failure_reason}
        </p>
      ) : null}
      {test.stderr ? (
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md border border-border bg-background p-2 text-xs text-muted-foreground">
          {test.stderr}
        </pre>
      ) : null}
    </li>
  )
}