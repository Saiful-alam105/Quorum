import {
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  type LucideIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/Badge"
import { cn } from "@/lib/utils"

type StatusConfig = {
  label: string
  icon: LucideIcon
  className: string
  spin: boolean
}

const analysisStatusConfig: Record<string, StatusConfig> = {
  pending: {
    label: "Queued",
    icon: Clock,
    className: "border-border bg-muted text-muted-foreground",
    spin: false,
  },
  in_progress: {
    label: "Running",
    icon: Loader2,
    className: "border-severity-low/40 bg-severity-low/15 text-severity-low",
    spin: true,
  },
  completed: {
    label: "Completed",
    icon: CheckCircle2,
    className: "border-success/40 bg-success/15 text-success",
    spin: false,
  },
  failed: {
    label: "Failed",
    icon: XCircle,
    className: "border-destructive/40 bg-destructive/15 text-destructive",
    spin: false,
  },
}

export function AnalysisStatusBadge({
  status,
  className,
}: {
  status: string | null | undefined
  className?: string
}) {
  const config =
    analysisStatusConfig[(status ?? "").toLowerCase()] ?? analysisStatusConfig.pending
  const Icon = config.icon
  return (
    <Badge variant="outline" className={cn(config.className, className)}>
      <Icon className={cn("h-3 w-3", config.spin && "animate-spin")} />
      {config.label}
    </Badge>
  )
}

export function PrStateBadge({
  state,
  className,
}: {
  state: string
  className?: string
}) {
  const isOpen = state === "open"
  return (
    <Badge variant={isOpen ? "success" : "muted"} className={cn("capitalize", className)}>
      {isOpen ? "Open" : state}
    </Badge>
  )
}