import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ArrowLeft,
  ClipboardCheck,
  ExternalLink,
  FolderGit2,
  GitPullRequest,
  Lock,
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
  getRepository,
  getRepositoryPullRequests,
  getReviews,
  isUnauthorized,
  type Finding,
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
      repository: Repository
      pullRequests: PullRequestSummary[]
      reviews: ReviewSummary[]
      findings: Finding[]
    }

export default function RepositoryDetailPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>()
  const id = Number(repositoryId)
  const [state, setState] = useState<PageState>({ status: "loading" })

  const load = useCallback(() => {
    if (!repositoryId || Number.isNaN(id)) {
      setState({ status: "error", message: "Invalid repository id" })
      return
    }

    setState({ status: "loading" })
    Promise.all([
      getRepository(id),
      getRepositoryPullRequests(id),
      getReviews(),
      getFindings(10),
    ])
      .then(([repository, pullRequests, reviews, findings]) =>
        setState({
          status: "ready",
          repository,
          pullRequests,
          reviews: reviews.filter((review) => review.repository_id === id),
          findings: findings.filter((finding) => finding.repository_id === id),
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
              : "Failed to load repository",
        })
      })
  }, [id, repositoryId])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-96" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
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

  const { repository, pullRequests, reviews, findings } = state

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
      <Link
        to="/repositories"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to repositories
      </Link>

      <div className="mb-6 space-y-1.5">
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-5 w-5 shrink-0 text-muted-foreground" />
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            {repository.full_name}
          </h1>
          {repository.is_private ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              Private
            </span>
          ) : null}
        </div>
        <p className="text-sm text-muted-foreground">
          Owner: {repository.owner}
        </p>
        <a
          href={`https://github.com/${repository.full_name}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          GitHub
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Pull Requests"
          value={pullRequests.length}
          icon={GitPullRequest}
        />
        <MetricCard
          label="Open Pull Requests"
          value={repository.open_pull_request_count}
          icon={GitPullRequest}
          accent="success"
        />
        <MetricCard
          label="Open Findings"
          value={openFindings}
          icon={ShieldCheck}
          accent={openFindings > 0 ? "warning" : "default"}
        />
        <MetricCard
          label="Reviews"
          value={reviews.length}
          icon={ClipboardCheck}
          accent={criticalFindings > 0 ? "critical" : "default"}
        />
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold">Pull Requests</h2>
      {pullRequests.length === 0 ? (
        <EmptyState
          icon={GitPullRequest}
          title="No Pull Requests yet"
          description="Pull Requests for this repository appear here after Quorum receives a webhook event."
        />
      ) : (
        <ul className="space-y-3">
          {pullRequests.map((pullRequest) => (
            <PullRequestReviewCard key={pullRequest.id} pullRequest={pullRequest} />
          ))}
        </ul>
      )}

      {findings.length > 0 ? (
        <>
          <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Findings</h2>
          <ul className="space-y-3">
            {findings.map((finding) => (
              <FindingListItem key={finding.id} finding={finding} />
            ))}
          </ul>
        </>
      ) : null}

      {reviews.length > 0 ? (
        <>
          <h2 className="mb-3 mt-8 text-lg font-semibold">Analysis Activity</h2>
          <ul className="space-y-3">
            {reviews.map((review) => (
              <ReviewListItem key={review.id} review={review} />
            ))}
          </ul>
        </>
      ) : null}
    </>
  )
}