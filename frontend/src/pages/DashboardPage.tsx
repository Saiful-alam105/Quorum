import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  ClipboardCheck,
  ExternalLink,
  FolderGit2,
  GitPullRequest,
  ShieldAlert,
} from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { LoadingState } from "@/components/LoadingState"
import { PageHeader } from "@/components/PageHeader"
import { SignInRequired } from "@/components/SignInRequired"
import { StatCard } from "@/components/StatCard"
import { getPullRequests, getRepositories, isUnauthorized } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { PullRequestSummary } from "@/lib/api"

type DashboardState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | {
      status: "ready"
      repositoryCount: number
      pullRequests: PullRequestSummary[]
    }

function PullRequestRow({ pullRequest }: { pullRequest: PullRequestSummary }) {
  const isOpen = pullRequest.state === "open"
  const prUrl = pullRequest.repository_full_name
    ? `https://github.com/${pullRequest.repository_full_name}/pull/${pullRequest.number}`
    : null

  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-border p-4">
      <div className="min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <GitPullRequest className="h-4 w-4 shrink-0 text-muted-foreground" />
          <Link
            to={`/pull-requests/${pullRequest.id}`}
            className="truncate font-medium transition-colors hover:text-primary hover:underline"
          >
            {pullRequest.repository_full_name ?? "unknown/repo"} #
            {pullRequest.number} {pullRequest.title}
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
        {prUrl ? (
          <a
            href={prUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            PR
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>
    </li>
  )
}

export default function DashboardPage() {
  const [state, setState] = useState<DashboardState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    Promise.all([getRepositories(), getPullRequests()])
      .then(([repositories, pullRequests]) =>
        setState({
          status: "ready",
          repositoryCount: repositories.length,
          pullRequests,
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

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your Quorum review activity."
      />

      {state.status === "loading" ? (
        <LoadingState label="Loading dashboard…" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState message={state.message} onRetry={load} />
      ) : null}

      {state.status === "auth-required" ? <SignInRequired /> : null}

      {state.status === "ready" ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Repositories"
              value={state.repositoryCount}
              icon={FolderGit2}
              available
            />
            <StatCard
              label="Pull Requests"
              value={state.pullRequests.length}
              icon={GitPullRequest}
              available
            />
            <StatCard
              label="Reviews"
              value={0}
              icon={ClipboardCheck}
              available={false}
            />
            <StatCard
              label="Warnings"
              value={0}
              icon={ShieldAlert}
              available={false}
            />
          </div>

          <h2 className="mb-3 mt-8 text-lg font-semibold">Recent Pull Requests</h2>

          {state.pullRequests.length === 0 ? (
            <EmptyState
              icon={GitPullRequest}
              title="No Pull Requests yet"
              description="Pull Requests appear here after Quorum receives a webhook event from the GitHub App. None have been stored yet."
            />
          ) : (
            <ul className="space-y-3">
              {state.pullRequests.map((pullRequest) => (
                <PullRequestRow key={pullRequest.id} pullRequest={pullRequest} />
              ))}
            </ul>
          )}
        </>
      ) : null}
    </>
  )
}