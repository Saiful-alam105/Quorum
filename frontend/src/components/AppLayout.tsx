import { NavLink, Outlet, useLocation } from "react-router-dom"
import { GitPullRequestArrow } from "lucide-react"

import { AuthStatus } from "@/components/AuthStatus"
import { BackendStatus } from "@/components/BackendStatus"
import { navItems } from "@/lib/navigation"
import { cn } from "@/lib/utils"

function QuorumMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/15 text-primary",
        className,
      )}
    >
      <GitPullRequestArrow className="h-4 w-4" />
    </span>
  )
}

export function AppLayout() {
  const { pathname } = useLocation()
  const current =
    navItems.find((item) =>
      item.to === "/" ? pathname === "/" : pathname.startsWith(item.to),
    ) ?? navItems[0]

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-16 shrink-0 flex-col border-r bg-card/40 lg:w-60">
        <div className="flex h-14 items-center justify-center gap-2 border-b px-3 lg:justify-start lg:px-4">
          <QuorumMark />
          <span className="hidden text-[15px] font-semibold tracking-tight lg:block">
            Quorum
          </span>
        </div>

        <nav className="flex-1 space-y-1 p-2 lg:p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              title={item.label}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors lg:px-3",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="hidden border-t p-4 text-xs text-muted-foreground lg:block">
          AI-powered Pull Request review
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b bg-background/80 px-4 backdrop-blur lg:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <QuorumMark className="lg:hidden" />
            <span className="hidden text-sm font-medium text-muted-foreground lg:block">
              {current.label}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <BackendStatus />
            <AuthStatus />
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}