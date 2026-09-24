import { useCallback, useEffect, useState } from "react"
import {
  ClipboardCheck,
  FolderGit2,
  GitPullRequest,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { FindingListItem } from "@/components/FindingListItem"
import { MetricCard } from "@/components/MetricCard"
import { PullRequestReviewCard } from "@/components/PullRequestReviewCard"
import { ReviewListItem } from "@/components/ReviewListItem"
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
    }

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
      getFindings(10),
    ])
      .then(([user, repositories, pullRequests, reviews, findings]) =>
        setState({
          status: "ready",
          user,
          repositoryCount: repositories.length,
          pullRequests,
          reviews,
          findings,
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

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Pull Requests</h2>
      {pullRequests.length === 0 ? (
        <EmptyState
          icon={GitPullRequest}
          title="No Pull Requests yet"
          description="Pull Requests appear here after Quorum receives a webhook event from the GitHub App."
        />
      ) : (
        <ul className="space-y-3">
          {pullRequests.slice(0, 8).map((pullRequest) => (
            <PullRequestReviewCard key={pullRequest.id} pullRequest={pullRequest} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Findings</h2>
      {findings.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No findings detected"
          description="Security findings from analyzed pull requests will appear here."
        />
      ) : (
        <ul className="space-y-3">
          {findings.map((finding) => (
            <FindingListItem key={finding.id} finding={finding} />
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
          {reviews.slice(0, 8).map((review) => (
            <ReviewListItem key={review.id} review={review} />
          ))}
        </ul>
      )}
    </>
  )
}