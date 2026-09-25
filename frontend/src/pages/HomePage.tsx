import { useEffect, useState } from "react"

import { AppLayout } from "@/components/AppLayout"
import { QuorumMark } from "@/components/QuorumMark"
import { getCurrentUser } from "@/lib/api"
import DashboardPage from "@/pages/DashboardPage"
import LandingPage from "@/pages/LandingPage"

type AuthState = "loading" | "anonymous" | "authenticated"

export default function HomePage() {
  const [auth, setAuth] = useState<AuthState>("loading")

  useEffect(() => {
    getCurrentUser()
      .then(() => setAuth("authenticated"))
      .catch(() => setAuth("anonymous"))
  }, [])

  if (auth === "loading") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background">
        <QuorumMark className="h-10 w-10 animate-pulse" />
        <span className="text-sm text-muted-foreground">Quorum</span>
      </div>
    )
  }

  if (auth === "anonymous") {
    return <LandingPage />
  }

  return (
    <AppLayout>
      <DashboardPage />
    </AppLayout>
  )
}