import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { ArrowLeft, ExternalLink, GitPullRequest } from "lucide-react"

import { ErrorState } from "@/components/ErrorState"
import { LoadingState } from "@/components/LoadingState"
import { getPullRequest, type PullRequestSummary } from "@/lib/api"
import { cn } from "@/lib/utils"

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; pullRequest: PullRequestSummary }

const notAvailableSections = [
  "Review summary",
  "Security findings",
  "Generated tests",
  "Coverage",
  "Changed files",
]

function NotAvailableSection({ title }: { title: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border p-6">
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-xs text-muted-foreground">Not yet available</p>
    </div>
  )
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
    getPullRequest(id)
      .then((pullRequest) => setState({ status: "ready", pullRequest }))
      .catch((error: unknown) =>
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Failed to load pull request",
        }),
      )
  }, [id, pullRequestId])

  useEffect(() => {
    load()
  }, [load])

  return (
    <>
      <Link
        to={
          state.status === "ready" && state.pullRequest.repository_id
            ? `/repositories/${state.pullRequest.repository_id}`
            : "/repositories"
        }
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to repository
      </Link>

      {state.status === "loading" ? (
        <LoadingState label="Loading pull request…" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState message={state.message} onRetry={load} />
      ) : null}

      {state.status === "ready" ? (
        <>
          <div className="mb-6 space-y-1">
            <div className="flex items-center gap-2">
              <GitPullRequest className="h-5 w-5 shrink-0 text-muted-foreground" />
              <h1 className="truncate text-2xl font-semibold tracking-tight">
                #{state.pullRequest.number} {state.pullRequest.title}
              </h1>
            </div>
            <p className="text-sm text-muted-foreground">
              {state.pullRequest.repository_full_name ?? "unknown/repo"}
            </p>
            <div className="flex items-center gap-3 pt-1">
              <span className="text-sm text-muted-foreground">
                Author: {state.pullRequest.author}
              </span>
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-xs font-medium",
                  state.pullRequest.state === "open"
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-muted text-muted-foreground",
                )}
              >
                {state.pullRequest.state}
              </span>
              {state.pullRequest.repository_full_name ? (
                <a
                  href={`https://github.com/${state.pullRequest.repository_full_name}/pull/${state.pullRequest.number}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  GitHub
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              ) : null}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {notAvailableSections.map((section) => (
              <NotAvailableSection key={section} title={section} />
            ))}
          </div>
        </>
      ) : null}
    </>
  )
}