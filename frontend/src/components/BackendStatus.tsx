import { useEffect, useState } from "react"
import { Activity, AlertCircle, Loader2 } from "lucide-react"

import { getHealth } from "@/lib/api"
import { cn } from "@/lib/utils"

type BackendStatus = "loading" | "connected" | "offline"

const statusConfig: Record<
  BackendStatus,
  { label: string; className: string; icon: typeof Activity }
> = {
  loading: {
    label: "Checking…",
    className: "border-border text-muted-foreground",
    icon: Loader2,
  },
  connected: {
    label: "Connected",
    className: "border-success/40 bg-success/10 text-success",
    icon: Activity,
  },
  offline: {
    label: "Backend offline",
    className: "border-destructive/40 bg-destructive/10 text-destructive",
    icon: AlertCircle,
  },
}

export function BackendStatus() {
  const [status, setStatus] = useState<BackendStatus>("loading")

  useEffect(() => {
    let active = true

    getHealth()
      .then((data) => {
        if (active) {
          setStatus(data.status === "ok" ? "connected" : "offline")
        }
      })
      .catch(() => {
        if (active) {
          setStatus("offline")
        }
      })

    return () => {
      active = false
    }
  }, [])

  const current = statusConfig[status]
  const StatusIcon = current.icon

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium",
        current.className,
      )}
    >
      <StatusIcon
        className={cn("h-3.5 w-3.5", status === "loading" && "animate-spin")}
      />
      <span>{current.label}</span>
    </div>
  )
}