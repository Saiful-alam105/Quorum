import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FolderGit2,
  GitMerge,
  GitPullRequest,
  GitPullRequestArrow,
  Loader2,
  MessageSquarePlus,
  ShieldCheck,
  TestTube2,
  X,
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
  closePullRequest,
  getPullRequest,
  getPullRequestAnalysis,
  getPullRequestCoverage,
  getPullRequestSecurity,
  getPullRequestTests,
  isUnauthorized,
  mergePullRequest,
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
  const [action, setAction] = useState<"merge" | "close" | null>(null)
  const [comment, setComment] = useState("")
  const [acting, setActing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

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

  const runMerge = useCallback(() => {
    setActing(true)
    setActionError(null)
    setActionMessage(null)
    mergePullRequest(id, comment.trim() || undefined)
      .then(() => {
        setAction(null)
        setComment("")
        setActionMessage("Pull request merged on GitHub.")
        load()
      })
      .catch((error: unknown) => {
        setActing(false)
        setActionError(
          error instanceof Error ? error.message : "Failed to merge the pull request",
        )
      })
  }, [id, comment, load])

  const runClose = useCallback(() => {
    setActing(true)
    setActionError(null)
    setActionMessage(null)
    closePullRequest(id)
      .then(() => {
        setAction(null)
        setActionMessage("Pull request closed on GitHub.")
        load()
      })
      .catch((error: unknown) => {
        setActing(false)
        setActionError(
          error instanceof Error ? error.message : "Failed to close the pull request",
        )
      })
  }, [id, load])

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

        {pullRequest.head_ref && pullRequest.base_ref ? (
          <p className="truncate font-mono text-sm text-muted-foreground">
            {pullRequest.head_ref}
            <span className="mx-1.5 text-foreground">→</span>
            {pullRequest.base_ref}
          </p>
        ) : null}
      </div>

      <div className="mb-8 rounded-lg border border-border bg-card p-4">
        <p className="mb-3 text-sm font-medium">Pull Request Actions</p>
        {actionMessage ? (
          <div className="mb-3 flex items-center gap-2 rounded-lg border border-success/40 bg-success/10 px-4 py-2 text-sm text-success">
            <CheckCircle2 className="h-4 w-4" />
            {actionMessage}
          </div>
        ) : null}
        {actionError ? (
          <div className="mb-3 flex items-center justify-between gap-3 rounded-lg border border-severity-critical/40 bg-severity-critical/10 px-4 py-2 text-sm text-severity-critical">
            <span>{actionError}</span>
            <button
              type="button"
              onClick={() => setActionError(null)}
              aria-label="Dismiss"
              className="inline-flex h-6 w-6 items-center justify-center rounded transition-colors hover:bg-accent"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : null}

        {pullRequest.state === "open" ? (
          <>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => {
                  setAction("merge")
                  setActionError(null)
                }}
                className="inline-flex items-center gap-1.5 rounded-md bg-success px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-success/90"
              >
                <GitMerge className="h-4 w-4" />
                Merge Pull Request
              </button>
              <button
                type="button"
                onClick={() => {
                  setAction("close")
                  setActionError(null)
                }}
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-severity-critical/40 hover:bg-severity-critical/10 hover:text-severity-critical"
              >
                <GitPullRequestArrow className="h-4 w-4" />
                Close Pull Request
              </button>
            </div>

            {action === "merge" ? (
              <div className="mt-4 space-y-3 rounded-lg border border-border p-4">
                <div>
                  <label
                    htmlFor="pr-merge-comment"
                    className="mb-1 block text-sm font-medium"
                  >
                    Merge message (optional)
                  </label>
                  <textarea
                    id="pr-merge-comment"
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    placeholder="This message is recorded on GitHub as the merge commit message."
                    rows={3}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Merges using a merge commit. Your message becomes the merge
                    commit message on GitHub.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={runMerge}
                    disabled={acting}
                    className="inline-flex items-center gap-1.5 rounded-md bg-success px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-success/90 disabled:opacity-50"
                  >
                    {acting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <GitMerge className="h-4 w-4" />
                    )}
                    {acting ? "Merging…" : "Confirm Merge"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAction(null)
                      setActionError(null)
                    }}
                    disabled={acting}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : null}

            {action === "close" ? (
              <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border border-border p-4">
                <p className="text-sm text-muted-foreground">
                  Close this pull request on GitHub without merging it?
                </p>
                <div className="flex shrink-0 items-center gap-3">
                  <button
                    type="button"
                    onClick={runClose}
                    disabled={acting}
                    className="inline-flex items-center gap-1.5 rounded-md border border-severity-critical/40 bg-severity-critical/10 px-4 py-2 text-sm font-medium text-severity-critical transition-colors hover:bg-severity-critical/20 disabled:opacity-50"
                  >
                    {acting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <GitPullRequestArrow className="h-4 w-4" />
                    )}
                    {acting ? "Closing…" : "Confirm Close"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAction(null)
                      setActionError(null)
                    }}
                    disabled={acting}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : null}
          </>
        ) : (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <MessageSquarePlus className="h-4 w-4" />
            This pull request is{" "}
            <span className="font-medium text-foreground">
              {pullRequest.state}
            </span>
            . No further actions are available.
          </p>
        )}
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