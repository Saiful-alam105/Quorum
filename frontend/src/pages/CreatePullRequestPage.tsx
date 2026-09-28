import { useCallback, useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, GitPullRequest, Loader2 } from "lucide-react"

import { ErrorState } from "@/components/ErrorState"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  createPullRequest,
  getRepository,
  getRepositoryBranches,
  isUnauthorized,
  type Repository,
} from "@/lib/api"

type PageState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; repository: Repository; branches: string[] }

export default function CreatePullRequestPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>()
  const id = Number(repositoryId)
  const navigate = useNavigate()
  const [state, setState] = useState<PageState>({ status: "loading" })
  const [head, setHead] = useState("")
  const [base, setBase] = useState("")
  const [title, setTitle] = useState("")
  const [body, setBody] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!repositoryId || Number.isNaN(id)) {
      setState({ status: "error", message: "Invalid repository id" })
      return
    }
    setState({ status: "loading" })
    Promise.all([getRepository(id), getRepositoryBranches(id)])
      .then(([repository, branches]) =>
        setState({ status: "ready", repository, branches }),
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

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (state.status !== "ready" || submitting) {
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    try {
      const created = await createPullRequest(id, {
        title: title.trim(),
        head: head.trim(),
        base: base.trim(),
        body: body.trim() || undefined,
      })
      navigate(`/pull-requests/${created.id}`)
    } catch (error: unknown) {
      setSubmitting(false)
      setSubmitError(
        error instanceof Error ? error.message : "Failed to create the pull request",
      )
    }
  }

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={load} />
  }

  if (state.status === "auth-required") {
    return <SignInRequired />
  }

  const { repository, branches } = state
  const canSubmit =
    title.trim().length > 0 && head.trim().length > 0 && base.trim().length > 0

  return (
    <>
      <Link
        to={`/repositories/${repository.id}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {repository.full_name}
      </Link>

      <div className="mb-6">
        <div className="flex items-center gap-2">
          <GitPullRequest className="h-5 w-5 shrink-0 text-muted-foreground" />
          <h1 className="text-2xl font-semibold tracking-tight">
            Create Pull Request
          </h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Create a real Pull Request on GitHub for {repository.full_name}.
        </p>
      </div>

      {branches.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-12 text-center text-sm text-muted-foreground">
          No branches found. Push a branch to GitHub first, then create a Pull
          Request here.
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="mx-auto max-w-2xl space-y-4 rounded-lg border border-border bg-card p-6"
        >
          <div>
            <label htmlFor="pr-source" className="mb-1 block text-sm font-medium">
              Source branch
            </label>
            <select
              id="pr-source"
              value={head}
              onChange={(event) => setHead(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            >
              <option value="">Select a branch…</option>
              {branches.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="pr-target" className="mb-1 block text-sm font-medium">
              Target branch
            </label>
            <select
              id="pr-target"
              value={base}
              onChange={(event) => setBase(event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            >
              <option value="">Select a branch…</option>
              {branches.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="pr-title" className="mb-1 block text-sm font-medium">
              Title
            </label>
            <input
              id="pr-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Add authentication"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label htmlFor="pr-body" className="mb-1 block text-sm font-medium">
              Description
            </label>
            <textarea
              id="pr-body"
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="What does this Pull Request change?"
              rows={5}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
          </div>

          {submitError ? (
            <p className="text-sm text-severity-critical">{submitError}</p>
          ) : null}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!canSubmit || submitting}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <GitPullRequest className="h-4 w-4" />
              )}
              {submitting ? "Creating…" : "Create Pull Request"}
            </button>
          </div>
        </form>
      )}
    </>
  )
}