import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  ClipboardCheck,
  FolderGit2,
  GitPullRequest,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { FindingCard } from "@/components/FindingCard"
import { MetricCard } from "@/components/MetricCard"
import { PullRequestReviewCard } from "@/components/PullRequestReviewCard"
import { ReviewCard } from "@/components/ReviewCard"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  getFindings,
  getMe,
  getPullRequests,
  getRepositories,
  getReviews,
  isUnauthorized,
  type CurrentUser,
  type Finding,
  type PullRequestSummary,
  type Repository,
  type ReviewSummary,
} from "@/lib/api"

type DashboardState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | {
      status: "ready"
      user: CurrentUser | null
      repositoryCount: number
      pullRequests: PullRequestSummary[]
      reviews: ReviewSummary[]
      findings: Finding[]
      repositories: Repository[]
    }

const RECENT_LIMIT = 4

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <div className="space-y-3">
        <Skeleton className="h-6 w-48" />
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-16" />
        ))}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [state, setState] = useState<DashboardState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    Promise.all([
      getMe(),
      getRepositories(),
      getPullRequests(),
      getReviews(),
      getFindings(RECENT_LIMIT),
    ])
      .then(([user, repositories, pullRequests, reviews, findings]) =>
        setState({
          status: "ready",
          user,
          repositoryCount: repositories.length,
          pullRequests,
          reviews,
          findings,
          repositories,
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
            error instanceof Error ? error.message : "Failed to load dashboard",
        })
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return <DashboardSkeleton />
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={load} />
  }

  if (state.status === "auth-required") {
    return <SignInRequired />
  }

  const {
    user,
    repositoryCount,
    pullRequests,
    reviews,
    findings,
    repositories,
  } = state

  const reviewsCompleted = reviews.filter(
    (review) => review.status === "completed",
  ).length
  const openFindings = pullRequests.reduce(
    (sum, pullRequest) => sum + pullRequest.finding_count,
    0,
  )
  const criticalFindings = pullRequests.reduce(
    (sum, pullRequest) => sum + pullRequest.critical_count,
    0,
  )
  const needsAttention = pullRequests.filter(
    (pullRequest) =>
      pullRequest.critical_count > 0 ||
      pullRequest.high_count > 0 ||
      pullRequest.latest_analysis_status === "failed",
  )

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Good to see you{user?.username ? `, ${user.username}` : ""}.
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {repositoryCount === 0
            ? "Quorum is ready. Connect repositories through the Quorum GitHub App to start analyzing pull requests."
            : `Quorum is monitoring ${repositoryCount} ${
                repositoryCount === 1 ? "repository" : "repositories"
              } and ${pullRequests.length} ${
                pullRequests.length === 1 ? "pull request" : "pull requests"
              }.`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          label="Repositories"
          value={repositoryCount}
          icon={FolderGit2}
        />
        <MetricCard
          label="Pull Requests"
          value={pullRequests.length}
          icon={GitPullRequest}
        />
        <MetricCard
          label="Reviews Completed"
          value={reviewsCompleted}
          icon={ClipboardCheck}
          accent="success"
        />
        <MetricCard
          label="Open Findings"
          value={openFindings}
          icon={ShieldCheck}
          accent={openFindings > 0 ? "warning" : "default"}
        />
        <MetricCard
          label="Critical Issues"
          value={criticalFindings}
          icon={ShieldAlert}
          accent={criticalFindings > 0 ? "critical" : "default"}
        />
      </div>

      <div className="mb-3 mt-8 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Your Repositories</h2>
        <Link
          to="/repositories"
          className="text-sm text-primary transition-colors hover:underline"
        >
          Connect repository
        </Link>
      </div>
      {repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories connected"
          description="Connect a GitHub repository to start reviewing Pull Requests with Quorum."
        />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {repositories.map((repository) => (
            <li key={repository.id}>
              <Link
                to={`/repositories/${repository.id}`}
                className="block space-y-1 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/40 hover:bg-accent/40"
              >
                <span className="flex items-center gap-2">
                  <FolderGit2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="truncate font-medium">
                    {repository.full_name}
                  </span>
                </span>
                <span className="block text-xs text-muted-foreground">
                  {repository.pull_request_count}{" "}
                  {repository.pull_request_count === 1 ? "PR" : "PRs"} ·{" "}
                  {repository.open_pull_request_count} open
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Pull Requests</h2>
      {pullRequests.length === 0 ? (
        <EmptyState
          icon={GitPullRequest}
          title="No Pull Requests yet"
          description="Pull Requests appear here after Quorum receives a webhook event from the GitHub App."
        />
      ) : (
        <ul className="space-y-3">
          {pullRequests.slice(0, RECENT_LIMIT).map((pullRequest) => (
            <PullRequestReviewCard key={pullRequest.id} pullRequest={pullRequest} />
          ))}
        </ul>
      )}

      {needsAttention.length > 0 ? (
        <>
          <h2 className="mb-3 mt-8 text-lg font-semibold">Needs attention</h2>
          <ul className="space-y-2">
            {needsAttention.slice(0, RECENT_LIMIT).map((pullRequest) => (
              <li key={pullRequest.id}>
                <Link
                  to={`/pull-requests/${pullRequest.id}`}
                  className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:border-primary/40 hover:bg-accent/40"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {pullRequest.repository_full_name ?? "unknown/repo"}{" "}
                      <span className="text-muted-foreground">
                        #{pullRequest.number}
                      </span>{" "}
                      {pullRequest.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {pullRequest.latest_analysis_status === "failed"
                        ? "Analysis failed"
                        : `${pullRequest.critical_count + pullRequest.high_count} high/critical finding${
                            pullRequest.critical_count + pullRequest.high_count === 1
                              ? ""
                              : "s"
                          }`}
                    </p>
                  </div>
                  <TriangleAlert className="h-4 w-4 shrink-0 text-severity-critical" />
                </Link>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Findings</h2>
      {findings.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No findings detected"
          description="Security findings from analyzed pull requests will appear here."
        />
      ) : (
        <ul className="space-y-3">
          {findings.slice(0, RECENT_LIMIT).map((finding) => (
            <FindingCard key={finding.id} finding={finding} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Reviews</h2>
      {reviews.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="No analysis runs yet"
          description="Completed Quorum analyses will appear here with their Merge Readiness Scores."
        />
      ) : (
        <ul className="space-y-3">
          {reviews.slice(0, RECENT_LIMIT).map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </ul>
      )}
    </>
  )
}