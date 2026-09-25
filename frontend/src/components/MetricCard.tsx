import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type Accent = "default" | "critical" | "success" | "warning" | "muted"

const accentClasses: Record<Accent, string> = {
  default: "bg-primary/15 text-primary",
  critical: "bg-severity-critical/15 text-severity-critical",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  muted: "bg-muted text-muted-foreground",
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  accent = "default",
  hint,
}: {
  label: string
  value: number | string
  icon: LucideIcon
  accent?: Accent
  hint?: string
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
            accentClasses[accent],
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  )
}