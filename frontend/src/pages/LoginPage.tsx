import { useState } from "react"
import { GitPullRequestArrow, Github, Loader2 } from "lucide-react"

import { getLoginUrl } from "@/lib/api"

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async () => {
    setLoading(true)
    setError(null)
    try {
      const { authorize_url } = await getLoginUrl()
      window.location.href = authorize_url
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start login")
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-8">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border p-8 text-center">
        <div className="space-y-2">
          <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
            <GitPullRequestArrow className="h-5 w-5" />
          </span>
          <h1 className="text-2xl font-bold tracking-tight">Quorum</h1>
          <p className="text-sm text-muted-foreground">
            Sign in with GitHub to review your Pull Requests.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLogin}
          disabled={loading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Github className="h-4 w-4" />
          )}
          {loading ? "Redirecting…" : "Continue with GitHub"}
        </button>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </div>
    </main>
  )
}
