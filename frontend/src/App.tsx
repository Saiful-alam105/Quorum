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

export default function App() {
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
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background p-8 text-center">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Quorum</h1>
        <p className="text-muted-foreground">
          AI-powered Pull Request review system
        </p>
      </div>

      <div
        className={cn(
          "flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm",
          current.className,
        )}
      >
        <StatusIcon
          className={cn("h-4 w-4", status === "loading" && "animate-spin")}
        />
        <span>{current.label}</span>
      </div>

      <p className="max-w-md text-xs text-muted-foreground">
        Frontend foundation (Chunk 0). Dashboard pages, authentication UI, and
        review views are not available yet.
      </p>
    </main>
  )
}
