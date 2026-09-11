import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { LogIn, LogOut } from "lucide-react"

import { getCurrentUser, logout, type CurrentUser } from "@/lib/api"

type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: CurrentUser }

export function AuthStatus() {
  const [state, setState] = useState<AuthState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getCurrentUser()
      .then((user) => setState({ status: "authenticated", user }))
      .catch(() => setState({ status: "anonymous" }))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSignOut = async () => {
    try {
      await logout()
    } finally {
      load()
    }
  }

  if (state.status === "loading") {
    return <span className="text-xs text-muted-foreground">…</span>
  }

  if (state.status === "anonymous") {
    return (
      <Link
        to="/login"
        className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-accent"
      >
        <LogIn className="h-3.5 w-3.5" />
        Sign in
      </Link>
    )
  }

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="font-medium">{state.user.username}</span>
      <button
        type="button"
        onClick={handleSignOut}
        className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 font-medium transition-colors hover:bg-accent"
      >
        <LogOut className="h-3.5 w-3.5" />
        Sign out
      </button>
    </div>
  )
}
