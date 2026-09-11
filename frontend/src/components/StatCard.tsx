import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type StatCardProps = {
  label: string
  value: number
  icon: LucideIcon
  available: boolean
}

export function StatCard({ label, value, icon: Icon, available }: StatCardProps) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <p
        className={cn(
          "mt-2 text-3xl font-semibold tracking-tight",
          !available && "text-muted-foreground",
        )}
      >
        {available ? value : "—"}
      </p>
      {!available ? (
        <p className="mt-1 text-xs text-muted-foreground">Not yet available</p>
      ) : null}
    </div>
  )
}