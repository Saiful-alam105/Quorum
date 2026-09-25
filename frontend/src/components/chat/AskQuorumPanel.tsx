import { MessageSquare, X } from "lucide-react"

export function AskQuorumPanel({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  if (!open) {
    return null
  }

  return (
    <div
      role="dialog"
      aria-label="Ask Quorum"
      className="fixed bottom-20 left-4 z-50 flex h-[28rem] w-[22rem] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl"
    >
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/15 text-primary">
            <MessageSquare className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold">Ask Quorum</p>
            <p className="truncate text-xs text-muted-foreground">
              Grounded in your reviews
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Ask Quorum"
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 text-sm text-muted-foreground">
        Select a review to start asking questions.
      </div>
    </div>
  )
}