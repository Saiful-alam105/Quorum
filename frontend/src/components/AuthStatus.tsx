import { useCallback, useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { ChevronDown, LogIn, LogOut, Settings } from "lucide-react"

import { Avatar } from "@/components/Avatar"
import { getCurrentUser, logout, type CurrentUser } from "@/lib/api"
import { cn } from "@/lib/utils"

type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: CurrentUser }

export function AuthStatus() {
  const [state, setState] = useState<AuthState>({ status: "loading" })
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const load = useCallback(() => {
    setState({ status: "loading" })
    getCurrentUser()
      .then((user) => setState({ status: "authenticated", user }))
      .catch(() => setState({ status: "anonymous" }))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!open) {
      return
    }
    const onPointerDown = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("mousedown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  const handleSignOut = async () => {
    setOpen(false)
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
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className={cn(
          "flex items-center gap-2 rounded-md border border-border py-1 pl-1 pr-2 text-sm font-medium transition-colors hover:bg-accent",
          open && "bg-accent",
        )}
      >
        <Avatar name={state.user.username} src={state.user.avatar_url} />
        <span className="hidden max-w-40 truncate sm:block">
          {state.user.username}
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 w-56 rounded-md border border-border bg-popover p-1 text-sm shadow-lg"
        >
          <Link
            to="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 rounded px-3 py-2 transition-colors hover:bg-accent"
          >
            <Avatar
              name={state.user.username}
              src={state.user.avatar_url}
              size="md"
            />
            <div className="min-w-0">
              <p className="truncate font-medium">{state.user.username}</p>
              <p className="truncate text-xs text-muted-foreground">
                Signed in with GitHub
              </p>
            </div>
          </Link>
          <div className="my-1 border-t border-border" />
          <Link
            to="/settings"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="mt-1 flex items-center gap-2 rounded px-3 py-2 transition-colors hover:bg-accent"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-left transition-colors hover:bg-accent"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  )
}