import {
  CircleAlert,
  Info,
  ShieldAlert,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/Badge"
import { cn } from "@/lib/utils"

export type SeverityLevel = "critical" | "high" | "medium" | "low" | "info"

type SeverityConfig = {
  label: string
  icon: LucideIcon
  badgeClass: string
  dotClass: string
}

export const severityConfig: Record<SeverityLevel, SeverityConfig> = {
  critical: {
    label: "Critical",
    icon: ShieldAlert,
    badgeClass:
      "border-severity-critical/40 bg-severity-critical/15 text-severity-critical",
    dotClass: "bg-severity-critical",
  },
  high: {
    label: "High",
    icon: TriangleAlert,
    badgeClass:
      "border-severity-high/40 bg-severity-high/15 text-severity-high",
    dotClass: "bg-severity-high",
  },
  medium: {
    label: "Medium",
    icon: CircleAlert,
    badgeClass:
      "border-severity-medium/40 bg-severity-medium/15 text-severity-medium",
    dotClass: "bg-severity-medium",
  },
  low: {
    label: "Low",
    icon: Info,
    badgeClass: "border-severity-low/40 bg-severity-low/15 text-severity-low",
    dotClass: "bg-severity-low",
  },
  info: {
    label: "Info",
    icon: Info,
    badgeClass: "border-severity-info/40 bg-severity-info/15 text-severity-info",
    dotClass: "bg-severity-info",
  },
}

export function normalizeSeverity(
  value: string | null | undefined,
): SeverityLevel {
  const normalized = (value ?? "").toLowerCase().trim()
  if (normalized in severityConfig) {
    return normalized as SeverityLevel
  }
  if (normalized === "error" || normalized === "blocker") {
    return "critical"
  }
  return "info"
}

export function SeverityBadge({
  severity,
  className,
}: {
  severity: string | null | undefined
  className?: string
}) {
  const config = severityConfig[normalizeSeverity(severity)]
  const Icon = config.icon
  return (
    <Badge variant="outline" className={cn("uppercase", config.badgeClass, className)}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}

export function SeverityDot({
  severity,
  className,
}: {
  severity: string | null | undefined
  className?: string
}) {
  const config = severityConfig[normalizeSeverity(severity)]
  return (
    <span
      aria-hidden="true"
      className={cn("inline-block h-2 w-2 rounded-full", config.dotClass, className)}
    />
  )
}