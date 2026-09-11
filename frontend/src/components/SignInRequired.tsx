import { Link } from "react-router-dom"
import { Lock, LogIn } from "lucide-react"

export function SignInRequired() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-12 text-center">
      <Lock className="h-10 w-10 text-muted-foreground" />
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">Sign in required</h2>
        <p className="max-w-md text-sm text-muted-foreground">
          You need to sign in with GitHub to view this data.
        </p>
      </div>
      <Link
        to="/login"
        className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        <LogIn className="h-4 w-4" />
        Sign in with GitHub
      </Link>
    </div>
  )
}