import { useCallback, useEffect, useState } from "react"
import { ShieldCheck, ShieldAlert } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { FindingCard } from "@/components/FindingCard"
import { MetricCard } from "@/components/MetricCard"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import { getFindings, isUnauthorized, type Finding } from "@/lib/api"
import { normalizeSeverity, type SeverityLevel } from "@/components/severity"

type FindingsState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; findings: Finding[] }

export default function FindingsPage() {
  const [state, setState] = useState<FindingsState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getFindings(100)
      .then((findings) => setState({ status: "ready", findings }))
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          setState({ status: "auth-required" })
          return
        }
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Failed to load findings",
        })
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-16" />
          ))}
        </div>
      </div>
    )
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={load} />
  }

  if (state.status === "auth-required") {
    return <SignInRequired />
  }

  const { findings } = state

  const counts = findings.reduce<Record<SeverityLevel, number>>(
    (acc, finding) => {
      acc[normalizeSeverity(finding.severity)] += 1
      return acc
    },
    { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
  )

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Findings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Security findings from the latest analysis of each pull request.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Critical"
          value={counts.critical}
          icon={ShieldAlert}
          accent={counts.critical > 0 ? "critical" : "muted"}
        />
        <MetricCard
          label="High"
          value={counts.high}
          icon={ShieldAlert}
          accent={counts.high > 0 ? "warning" : "muted"}
        />
        <MetricCard
          label="Medium"
          value={counts.medium}
          icon={ShieldCheck}
          accent={counts.medium > 0 ? "warning" : "muted"}
        />
        <MetricCard
          label="Low"
          value={counts.low + counts.info}
          icon={ShieldCheck}
          accent="muted"
        />
      </div>

      {findings.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={ShieldCheck}
            title="No findings detected"
            description="Security findings from analyzed pull requests will appear here."
          />
        </div>
      ) : (
        <ul className="mt-8 space-y-3">
          {findings.map((finding) => (
            <FindingCard key={finding.id} finding={finding} />
          ))}
        </ul>
      )}
    </>
  )
}