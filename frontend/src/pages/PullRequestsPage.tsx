import { useCallback, useEffect, useState } from "react"
import { GitPullRequest } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { PullRequestReviewCard } from "@/components/PullRequestReviewCard"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import { getPullRequests, isUnauthorized, type PullRequestSummary } from "@/lib/api"

type PullRequestsState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; pullRequests: PullRequestSummary[] }

export default function PullRequestsPage() {
  const [state, setState] = useState<PullRequestsState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getPullRequests()
      .then((pullRequests) => setState({ status: "ready", pullRequests }))
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
              : "Failed to load pull requests",
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

  const { pullRequests } = state

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Pull Requests</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pull Requests received from GitHub webhooks.
        </p>
      </div>

      {pullRequests.length === 0 ? (
        <EmptyState
          icon={GitPullRequest}
          title="No Pull Requests yet"
          description="Pull Requests appear here after Quorum receives a webhook event from the GitHub App."
        />
      ) : (
        <ul className="space-y-3">
          {pullRequests.map((pullRequest) => (
            <PullRequestReviewCard key={pullRequest.id} pullRequest={pullRequest} />
          ))}
        </ul>
      )}
    </>
  )
}