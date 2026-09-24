import { ClipboardCheck } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import type { CoverageResult } from "@/lib/api"

export function CoverageBlock({ coverage }: { coverage: CoverageResult | null }) {
  if (!coverage) {
    return (
      <EmptyState
        icon={ClipboardCheck}
        title="Coverage not measured"
        description="Coverage was not measured for this analysis run."
      />
    )
  }
  const rows = [
    { label: "Before", value: coverage.coverage_before },
    { label: "After", value: coverage.coverage_after },
    { label: "Delta", value: coverage.coverage_delta },
  ]
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {rows.map((row) => (
        <div key={row.label} className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">{row.label}</p>
          <p className="mt-1 font-mono text-2xl font-semibold">
            {row.value != null ? `${row.value.toFixed(1)}%` : "—"}
          </p>
        </div>
      ))}
    </div>
  )
}