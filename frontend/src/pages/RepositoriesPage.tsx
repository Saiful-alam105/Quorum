import { useCallback, useEffect, useState } from "react"
import { FolderGit2 } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { RepositoryListItem } from "@/components/RepositoryListItem"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import { getRepositories, isUnauthorized, type Repository } from "@/lib/api"

type RepositoriesState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; repositories: Repository[] }

export default function RepositoriesPage() {
  const [state, setState] = useState<RepositoriesState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getRepositories()
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

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
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

  const { repositories } = state

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Repositories</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Repositories connected through the Quorum GitHub App.
        </p>
      </div>

      {repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories yet"
          description="Repositories appear here after Quorum receives a webhook event from the GitHub App."
        />
      ) : (
        <ul className="space-y-3">
          {repositories.map((repository) => (
            <RepositoryListItem key={repository.id} repository={repository} />
          ))}
        </ul>
      )}
    </>
  )
}