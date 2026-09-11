import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ArrowLeft,
  ExternalLink,
  GitPullRequest,
  Lock,
} from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { LoadingState } from "@/components/LoadingState"
import { SignInRequired } from "@/components/SignInRequired"
import {
  getRepository,
  getRepositoryPullRequests,
  isUnauthorized,
  type PullRequest,
  type Repository,
} from "@/lib/api"
import { cn } from "@/lib/utils"

type PageState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; repository: Repository; pullRequests: PullRequest[] }

function PullRequestCard({
  repository,
  pullRequest,
}: {
  repository: Repository
  pullRequest: PullRequest
}) {
  const isOpen = pullRequest.state === "open"

  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-border p-4">
      <div className="min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <GitPullRequest className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Link
            to={`/pull-requests/${pullRequest.id}`}
            className="truncate font-medium transition-colors hover:text-primary hover:underline"
          >
            #{pullRequest.number} {pullRequest.title}
          </Link>
        </div>
        <p className="text-xs text-muted-foreground">
          Author: {pullRequest.author}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            isOpen
              ? "bg-emerald-100 text-emerald-700"
              : "bg-muted text-muted-foreground",
          )}
        >
          {pullRequest.state}
        </span>
        <a
          href={`https://github.com/${repository.full_name}/pull/${pullRequest.number}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          PR
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </li>
  )
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
    Promise.all([getRepository(id), getRepositoryPullRequests(id)])
      .then(([repository, pullRequests]) =>
        setState({ status: "ready", repository, pullRequests }),
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

  return (
    <>
      <Link
        to="/repositories"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to repositories
      </Link>

      {state.status === "loading" ? (
        <LoadingState label="Loading repository…" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState message={state.message} onRetry={load} />
      ) : null}

      {state.status === "auth-required" ? <SignInRequired /> : null}

      {state.status === "ready" ? (
        <>
          <div className="mb-6 space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">
                {state.repository.full_name}
              </h1>
              {state.repository.is_private ? (
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  <Lock className="h-3 w-3" />
                  Private
                </span>
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground">
              Owner: {state.repository.owner}
            </p>
            <a
              href={`https://github.com/${state.repository.full_name}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              GitHub
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>

          <h2 className="mb-3 text-lg font-semibold">Pull Requests</h2>

          {state.pullRequests.length === 0 ? (
            <EmptyState
              icon={GitPullRequest}
              title="No Pull Requests yet"
              description="Pull Requests for this repository appear here after Quorum receives a webhook event. None have been stored yet."
            />
          ) : (
            <ul className="space-y-3">
              {state.pullRequests.map((pullRequest) => (
                <PullRequestCard
                  key={pullRequest.id}
                  repository={state.repository}
                  pullRequest={pullRequest}
                />
              ))}
            </ul>
          )}
        </>
      ) : null}
    </>
  )
}