import { Link } from "react-router-dom"

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

        <Link
          to="/login"
          className={cn(buttonVariants({ size: "sm" }), "shrink-0")}
        >
          Sign in with GitHub
        </Link>
      </div>
    </header>
  )
}