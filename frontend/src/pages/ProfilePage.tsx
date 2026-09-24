import { useCallback, useEffect, useState } from "react"
import { ClipboardCheck, FolderGit2, GitPullRequest, ShieldCheck } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { MetricCard } from "@/components/MetricCard"
import { ProfileCard } from "@/components/ProfileCard"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  getMe,
  getPullRequests,
  getRepositories,
  getReviews,
  isUnauthorized,
  type CurrentUser,
  type PullRequestSummary,
  type Repository,
  type ReviewSummary,
} from "@/lib/api"

type PageState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | {
      status: "ready"
      user: CurrentUser
      repositories: Repository[]
      pullRequests: PullRequestSummary[]
      reviews: ReviewSummary[]
    }

export default function ProfilePage() {
  const [state, setState] = useState<PageState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    Promise.all([
      getMe(),
      getRepositories(),
      getPullRequests(),
      getReviews(),
    ])
      .then(([user, repositories, pullRequests, reviews]) =>
        setState({ status: "ready", user, repositories, pullRequests, reviews }),
      )
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          setState({ status: "auth-required" })
          return
        }
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Failed to load profile",
        })
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={load} />
  }

  if (state.status === "auth-required") {
    return <SignInRequired />
  }

  const { user, repositories, pullRequests, reviews } = state

  const reviewsCompleted = reviews.filter(
    (review) => review.status === "completed",
  ).length
  const openFindings = pullRequests.reduce(
    (sum, pullRequest) => sum + pullRequest.finding_count,
    0,
  )

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your Quorum account and activity.
        </p>
      </div>

      <ProfileCard user={user} />

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Repositories"
          value={repositories.length}
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
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold">Connected Repositories</h2>
      {repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories connected"
          description="Repositories appear here after the Quorum GitHub App is installed and a webhook event is received."
        />
      ) : (
        <ul className="space-y-2">
          {repositories.map((repository) => (
            <li
              key={repository.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3 text-sm"
            >
              <span className="truncate">{repository.full_name}</span>
              {repository.is_private ? (
                <span className="shrink-0 text-xs text-muted-foreground">
                  Private
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
