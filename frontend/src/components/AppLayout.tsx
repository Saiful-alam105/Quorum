import { useState, type ReactNode } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { PanelLeftClose, PanelLeftOpen } from "lucide-react"

import { AuthStatus } from "@/components/AuthStatus"
import { BackendStatus } from "@/components/BackendStatus"
import { AskQuorum } from "@/components/chat/AskQuorum"
import { QuorumMark } from "@/components/QuorumMark"
import { navItems } from "@/lib/navigation"
import { cn } from "@/lib/utils"

export function AppLayout({ children }: { children?: ReactNode }) {
  const { pathname } = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const current =
    navItems.find((item) =>
      item.to === "/" ? pathname === "/" : pathname.startsWith(item.to),
    ) ?? navItems[0]

  return (
    <div className="flex min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:border focus:border-border focus:bg-background focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>
      <aside
        className={cn(
          "flex shrink-0 flex-col border-r bg-card/40 transition-[width] duration-200 ease-out",
          collapsed ? "w-16" : "w-16 lg:w-60",
        )}
      >
        <Link
          to="/"
          aria-label="Quorum home"
          className={cn(
            "flex h-14 items-center gap-2 border-b px-3 transition-colors hover:bg-accent",
            collapsed ? "justify-center" : "justify-center lg:justify-start lg:px-4",
          )}
        >
          <QuorumMark />
          <span
            className={cn(
              "hidden text-[15px] font-semibold tracking-tight",
              !collapsed && "lg:block",
            )}
          >
            Quorum
          </span>
        </Link>

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
                  collapsed && "justify-center",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span
                className={cn("hidden", !collapsed && "lg:block")}
              >
                {item.label}
              </span>
            </NavLink>
          ))}
        </nav>

        <div
          className={cn(
            "hidden border-t p-4 text-xs text-muted-foreground",
            !collapsed && "lg:block",
          )}
        >
          AI-powered Pull Request review
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b bg-background/80 px-4 backdrop-blur lg:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setCollapsed((value) => !value)}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent"
            >
              {collapsed ? (
                <PanelLeftOpen className="h-4 w-4" />
              ) : (
                <PanelLeftClose className="h-4 w-4" />
              )}
            </button>
            <Link
              to="/"
              aria-label="Quorum home"
              className="flex items-center rounded-md transition-colors hover:bg-accent lg:hidden"
            >
              <QuorumMark className="m-1" />
            </Link>
            <span className="hidden text-sm font-medium text-muted-foreground lg:block">
              {current.label}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <BackendStatus />
            <AuthStatus />
          </div>
        </header>

        <main id="main-content" className="flex-1 p-4 lg:p-6">
          {children ?? <Outlet />}
        </main>
      </div>

      <AskQuorum />
    </div>
  )
}