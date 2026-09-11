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
    label: "Checking backend…",
    className: "text-muted-foreground",
    icon: Loader2,
  },
  connected: {
    label: "Backend connected",
    className: "text-emerald-600",
    icon: Activity,
  },
  offline: {
    label: "Backend offline",
    className: "text-destructive",
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
        "flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-xs",
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
