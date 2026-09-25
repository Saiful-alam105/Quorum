import { QuorumMark } from "@/components/QuorumMark"

export function LandingFooter() {
  return (
    <footer className="border-t bg-card/40">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between lg:px-6">
        <div className="flex items-center gap-2">
          <QuorumMark className="h-6 w-6" />
          <span className="font-semibold text-foreground">Quorum</span>
          <span className="hidden sm:inline">· AI-powered Pull Request review</span>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/Saiful-alam105/Quorum"
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            GitHub
          </a>
          <span>© {new Date().getFullYear()} Quorum</span>
        </div>
      </div>
    </footer>
  )
}