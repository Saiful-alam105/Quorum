import { useState } from "react"
import { Link } from "react-router-dom"
import { Menu, X } from "lucide-react"

import { QuorumMark } from "@/components/QuorumMark"
import { buttonVariants } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

const links = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#features", label: "Features" },
  { href: "#architecture", label: "Architecture" },
  { href: "#why-quorum", label: "Why Quorum" },
]

export function LandingNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 lg:px-6">
        <Link
          to="/"
          aria-label="Quorum home"
          className="flex items-center gap-2"
        >
          <QuorumMark />
          <span className="text-[15px] font-semibold tracking-tight">Quorum</span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex" aria-label="Landing">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className={cn(buttonVariants({ size: "sm" }), "hidden shrink-0 sm:inline-flex")}
          >
            Sign in with GitHub
          </Link>
          <button
            type="button"
            aria-label="Toggle navigation menu"
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent md:hidden"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {open ? (
        <nav className="border-t md:hidden" aria-label="Landing mobile">
          <div className="mx-auto max-w-6xl space-y-1 px-4 py-3 lg:px-6">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="block rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="block rounded-md px-3 py-2 text-sm font-medium text-primary transition-colors hover:bg-accent"
            >
              Sign in with GitHub
            </Link>
          </div>
        </nav>
      ) : null}
    </header>
  )
}