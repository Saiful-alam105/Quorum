import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ArrowLeft,
  ExternalLink,
  FolderGit2,
  GitPullRequest,
  ShieldCheck,
  TestTube2,
} from "lucide-react"

import { CoverageBlock } from "@/components/CoverageBlock"
import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { MergeReadinessBlock } from "@/components/MergeReadinessBlock"
import { SecurityFindingCard } from "@/components/SecurityFindingCard"
import { SignInRequired } from "@/components/SignInRequired"
import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"
import { TestRunItem } from "@/components/TestRunItem"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  getPullRequest,
  getPullRequestAnalysis,
  getPullRequestCoverage,
  getPullRequestSecurity,
  getPullRequestTests,
  isUnauthorized,
  type AnalysisRun,
  type CoverageResult,
  type PullRequestSummary,
  type SecurityFinding,
  type TestRun,
} from "@/lib/api"
import { formatDateTime, formatUpdatedAt } from "@/lib/format"

type PageState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | {
      status: "ready"
      pullRequest: PullRequestSummary
      runs: AnalysisRun[]
      findings: SecurityFinding[]
      tests: TestRun[]
      coverage: CoverageResult | null
    }

export default function PullRequestDetailPage() {
  const { pullRequestId } = useParams<{ pullRequestId: string }>()
  const id = Number(pullRequestId)
  const [state, setState] = useState<PageState>({ status: "loading" })

  const load = useCallback(() => {
    if (!pullRequestId || Number.isNaN(id)) {
      setState({ status: "error", message: "Invalid pull request id" })
      return
    }

    setState({ status: "loading" })
    Promise.all([
      getPullRequest(id),
      getPullRequestAnalysis(id),
      getPullRequestSecurity(id),
      getPullRequestTests(id),
      getPullRequestCoverage(id),
    ])
      .then(([pullRequest, runs, findings, tests, coverage]) =>
        setState({
          status: "ready",
          pullRequest,
          runs,
          findings,
          tests,
          coverage,
        }),
      )
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          setState({ status: "auth-required" })
          return
        }
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Failed to load pull request",
        })
      })
  }, [id, pullRequestId])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-96" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
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

  const { pullRequest, runs, findings, tests, coverage } = state
  const latestRun = runs.length > 0 ? runs[0] : null

  return (
    <>
      <Link
        to={
          pullRequest.repository_id
            ? `/repositories/${pullRequest.repository_id}`
            : "/repositories"
        }
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to repository
      </Link>

      <div className="mb-6 space-y-1.5">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FolderGit2 className="h-4 w-4" />
          {pullRequest.repository_id ? (
            <Link
              to={`/repositories/${pullRequest.repository_id}`}
              className="transition-colors hover:text-foreground"
            >
              {pullRequest.repository_full_name ?? "unknown/repo"}
            </Link>
          ) : (
            <span>{pullRequest.repository_full_name ?? "unknown/repo"}</span>
          )}
          <span>/</span>
          <span className="text-foreground">pull #{pullRequest.number}</span>
        </div>

        <div className="flex items-center gap-2">
          <GitPullRequest className="h-5 w-5 shrink-0 text-muted-foreground" />
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            {pullRequest.title}
          </h1>
          <PrStateBadge state={pullRequest.state} />
        </div>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
          <span>Author: {pullRequest.author}</span>
          {pullRequest.updated_at ? (
            <span>· Updated {formatUpdatedAt(pullRequest.updated_at)}</span>
          ) : null}
          {pullRequest.repository_full_name ? (
            <a
              href={`https://github.com/${pullRequest.repository_full_name}/pull/${pullRequest.number}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 transition-colors hover:text-foreground"
            >
              GitHub
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
        </div>
      </div>

      <div className="mb-8 grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <MergeReadinessBlock
            score={latestRun?.merge_readiness_score ?? null}
            recommendation={latestRun?.recommendation ?? null}
          />
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Analysis</p>
          <div className="mt-2">
            <AnalysisStatusBadge
              status={latestRun?.status ?? pullRequest.latest_analysis_status}
            />
          </div>
          {latestRun ? (
            <p className="mt-2 text-xs text-muted-foreground">
              {latestRun.completed_at
                ? `Completed ${formatDateTime(latestRun.completed_at)}`
                : latestRun.started_at
                  ? `Started ${formatDateTime(latestRun.started_at)}`
                  : "Queued"}
            </p>
          ) : null}
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Run Summary</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5 text-muted-foreground" />
              {findings.length} security{" "}
              {findings.length === 1 ? "finding" : "findings"}
            </p>
            <p>
              <TestTube2 className="mr-1 inline h-3.5 w-3.5 text-muted-foreground" />
              {tests.length} generated {tests.length === 1 ? "test" : "tests"}
            </p>
          </div>
        </div>
      </div>

      {runs.length > 0 ? (
        <>
          <h2 className="mb-3 text-lg font-semibold">Analysis History</h2>
          <ul className="space-y-2">
            {runs.map((run) => (
              <li
                key={run.id}
                className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <AnalysisStatusBadge status={run.status} />
                  <span className="text-xs text-muted-foreground">
                    Run #{run.id}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {run.merge_readiness_score != null ? (
                    <span className="font-mono text-sm font-semibold">
                      {run.merge_readiness_score}
                      <span className="text-xs text-muted-foreground">/100</span>
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">
                      No score
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {run.completed_at
                      ? formatDateTime(run.completed_at)
                      : "—"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Security Findings</h2>
      {findings.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No findings detected"
          description="No security findings were produced for this pull request."
        />
      ) : (
        <ul className="space-y-3">
          {findings.map((finding) => (
            <SecurityFindingCard key={finding.id} finding={finding} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Generated Tests</h2>
      {tests.length === 0 ? (
        <EmptyState
          icon={TestTube2}
          title="No tests generated"
          description="No generated tests were run for this pull request."
        />
      ) : (
        <ul className="space-y-3">
          {tests.map((test) => (
            <TestRunItem key={test.id} test={test} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Coverage</h2>
      <CoverageBlock coverage={coverage} />
    </>
  )
}