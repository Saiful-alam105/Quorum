import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FolderGit2, LogIn, LogOut, User as UserIcon } from "lucide-react"

import { ErrorState } from "@/components/ErrorState"
import { LoadingState } from "@/components/LoadingState"
import { PageHeader } from "@/components/PageHeader"
import {
  getMe,
  getRepositories,
  isUnauthorized,
  logout,
  type CurrentUser,
  type Repository,
} from "@/lib/api"

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; user: CurrentUser | null; repositories: Repository[] }

export default function SettingsPage() {
  const [state, setState] = useState<PageState>({ status: "loading" })

  const load = useCallback(async () => {
    setState({ status: "loading" })
    try {
      let user: CurrentUser | null = null
      try {
        user = await getMe()
      } catch (error) {
        if (isUnauthorized(error)) {
          user = null
        } else {
          throw error
        }
      }
      let repositories: Repository[] = []
      if (user) {
        try {
          repositories = await getRepositories()
        } catch (error) {
          if (!isUnauthorized(error)) {
            throw error
          }
        }
      }
      setState({ status: "ready", user, repositories })
    } catch (error) {
      setState({
        status: "error",
        message:
          error instanceof Error ? error.message : "Failed to load settings",
      })
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSignOut = async () => {
    try {
      await logout()
    } finally {
      window.location.reload()
    }
  }

  return (
    <>
      <PageHeader
        title="Settings"
        description="Your GitHub account, connected repositories, and preferences."
      />

      {state.status === "loading" ? (
        <LoadingState label="Loading settings…" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState message={state.message} onRetry={load} />
      ) : null}

      {state.status === "ready" ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-lg border border-border p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <UserIcon className="h-5 w-5 text-muted-foreground" />
              GitHub Account
            </h2>

            {state.user ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Username</p>
                  <p className="font-medium">{state.user.username}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">GitHub ID</p>
                  <p className="font-medium">{state.user.github_id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    GitHub App authorization
                  </p>
                  <p className="font-medium text-emerald-600">Authorized</p>
                </div>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  You are not signed in.
                </p>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  <LogIn className="h-4 w-4" />
                  Sign in with GitHub
                </Link>
              </div>
            )}
          </section>

          <section className="rounded-lg border border-border p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <FolderGit2 className="h-5 w-5 text-muted-foreground" />
              Connected Repositories
            </h2>

            {state.repositories.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No repositories connected yet. Repositories appear here after
                Quorum receives a webhook event from the GitHub App.
              </p>
            ) : (
              <ul className="space-y-2">
                {state.repositories.map((repository) => (
                  <li
                    key={repository.id}
                    className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
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
          </section>
        </div>
      ) : null}
    </>
  )
}