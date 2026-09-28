import { useCallback, useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { CheckCircle2, FolderGit2, Lock, Search, Unplug } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  getDiscoveredRepositories,
  isUnauthorized,
  type DiscoveredRepository,
} from "@/lib/api"
import { cn } from "@/lib/utils"

type Filter = "all" | "connected" | "needs"

type RepositoriesState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; repositories: DiscoveredRepository[] }

const filters: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "connected", label: "Connected" },
  { value: "needs", label: "Needs connection" },
]

function RepositoryCard({
  repository,
}: {
  repository: DiscoveredRepository
}) {
  const content = (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0 space-y-1.5">
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate font-medium">{repository.full_name}</span>
          {repository.is_private ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              Private
            </span>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">
          {repository.language ?? "Unknown language"}
          {repository.default_branch
            ? ` · default branch: ${repository.default_branch}`
            : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {repository.connected ? (
          <>
            <span className="text-xs text-muted-foreground">
              {repository.pull_request_count}{" "}
              {repository.pull_request_count === 1 ? "PR" : "PRs"}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-success/40 bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
              <CheckCircle2 className="h-3 w-3" />
              Connected
            </span>
          </>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs font-medium text-muted-foreground">
            <Unplug className="h-3 w-3" />
            Needs connection
          </span>
        )}
      </div>
    </div>
  )

  const className =
    "block rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/40 hover:bg-accent/40"

  return repository.connected && repository.id != null ? (
    <Link to={`/repositories/${repository.id}`} className={className}>
      {content}
    </Link>
  ) : (
    <div className={className}>{content}</div>
  )
}

export default function RepositoriesPage() {
  const [state, setState] = useState<RepositoriesState>({ status: "loading" })
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState<Filter>("all")

  const load = useCallback(() => {
    setState({ status: "loading" })
    getDiscoveredRepositories()
      .then((repositories) => setState({ status: "ready", repositories }))
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
              : "Failed to load repositories",
        })
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const visible = useMemo(() => {
    if (state.status !== "ready") {
      return []
    }
    const needle = query.trim().toLowerCase()
    return state.repositories.filter((repository) => {
      if (filter === "connected" && !repository.connected) return false
      if (filter === "needs" && repository.connected) return false
      if (needle && !repository.full_name.toLowerCase().includes(needle)) {
        return false
      }
      return true
    })
  }, [state, query, filter])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
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

  const { repositories } = state

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Repositories</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Choose a GitHub repository to open its Quorum workspace.
        </p>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search repositories..."
            aria-label="Search repositories"
            className="w-full rounded-md border border-border bg-background py-1.5 pl-9 pr-3 text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          {filters.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFilter(option.value)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                filter === option.value
                  ? "border-primary/40 bg-primary/15 text-primary"
                  : "border-border text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories found"
          description="Quorum could not find any GitHub repositories for your account. Make sure you are signed in with GitHub."
        />
      ) : visible.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="Nothing matches"
          description="No repositories match your search or filter."
        />
      ) : (
        <ul className="space-y-3">
          {visible.map((repository) => (
            <li key={repository.github_id}>
              <RepositoryCard repository={repository} />
            </li>
          ))}
        </ul>
      )}
    </>
  )
}