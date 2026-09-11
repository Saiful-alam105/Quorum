import { useCallback, useEffect, useState } from "react"
import { ExternalLink, FolderGit2, Lock } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { LoadingState } from "@/components/LoadingState"
import { PageHeader } from "@/components/PageHeader"
import { getRepositories, type Repository } from "@/lib/api"

type RepositoriesState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; repositories: Repository[] }

function RepositoryCard({ repository }: { repository: Repository }) {
  return (
    <li className="flex items-center justify-between gap-4 rounded-lg border border-border p-4">
      <div className="min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate font-medium">{repository.full_name}</span>
          {repository.is_private ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              Private
            </span>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">Owner: {repository.owner}</p>
      </div>
      <a
        href={`https://github.com/${repository.full_name}`}
        target="_blank"
        rel="noreferrer"
        className="inline-flex shrink-0 items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        GitHub
        <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </li>
  )
}

export default function RepositoriesPage() {
  const [state, setState] = useState<RepositoriesState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getRepositories()
      .then((repositories) => setState({ status: "ready", repositories }))
      .catch((error: unknown) =>
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Failed to load repositories",
        }),
      )
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <>
      <PageHeader
        title="Repositories"
        description="Repositories connected through the Quorum GitHub App."
      />

      {state.status === "loading" ? (
        <LoadingState label="Loading repositories…" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState message={state.message} onRetry={load} />
      ) : null}

      {state.status === "ready" && state.repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories yet"
          description="Repositories appear here after Quorum receives a webhook event from the GitHub App. None have been stored yet."
        />
      ) : null}

      {state.status === "ready" && state.repositories.length > 0 ? (
        <ul className="space-y-3">
          {state.repositories.map((repository) => (
            <RepositoryCard key={repository.id} repository={repository} />
          ))}
        </ul>
      ) : null}
    </>
  )
}
