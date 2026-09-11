import { NavLink, Outlet } from "react-router-dom"
import { Activity } from "lucide-react"

import { BackendStatus } from "@/components/BackendStatus"
import { navItems } from "@/lib/navigation"
import { cn } from "@/lib/utils"

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="flex w-64 shrink-0 flex-col border-r bg-muted/40">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <Activity className="h-6 w-6 text-primary" />
          <span className="text-lg font-bold tracking-tight">Quorum</span>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t p-4 text-xs text-muted-foreground">
          Quorum Web Dashboard
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-end border-b px-6">
          <BackendStatus />
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
