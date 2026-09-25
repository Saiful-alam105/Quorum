import { MessageSquare } from "lucide-react"

import { cn } from "@/lib/utils"

export function AskQuorumButton({
  open,
  onToggle,
}: {
  open: boolean
  onToggle: () => void
}) {
  return (
    <div className="group relative">
      <button
        type="button"
        onClick={onToggle}
        aria-label="Ask Quorum"
        aria-expanded={open}
        aria-haspopup="dialog"
        className={cn(
          "flex h-12 w-12 items-center justify-center rounded-xl border border-primary/40 bg-primary/15 text-primary shadow-lg shadow-primary/10 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary/25 hover:shadow-primary/20",
          open && "bg-primary/25",
        )}
      >
        <MessageSquare className="h-5 w-5" />
      </button>
      <span
        className="pointer-events-none absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md border border-border bg-popover px-2 py-1 text-xs text-popover-foreground opacity-0 shadow transition-opacity duration-150 group-hover:opacity-100"
        role="tooltip"
      >
        Ask Quorum
      </span>
    </div>
  )
}