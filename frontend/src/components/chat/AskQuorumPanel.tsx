import { ExternalLink, MessageSquare, X } from "lucide-react"
import type { Dispatch, SetStateAction } from "react"

import { QuorumChat } from "@/components/chat/QuorumChat"
import type { ChatMessage } from "@/lib/api"

export function AskQuorumPanel({
  open,
  onClose,
  onOpenPage,
  selectedReviewId,
  onSelectedReviewChange,
  messages,
  setMessages,
}: {
  open: boolean
  onClose: () => void
  onOpenPage: () => void
  selectedReviewId: number | null
  onSelectedReviewChange: (id: number | null) => void
  messages: ChatMessage[]
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
}) {
  if (!open) {
    return null
  }

  return (
    <div
      role="dialog"
      aria-label="Ask Quorum"
      className="fixed bottom-20 right-4 z-50 flex h-[28rem] w-[22rem] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl"
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
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={onOpenPage}
            aria-label="Open Ask Quorum in full page"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close Ask Quorum"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <QuorumChat
        selectedReviewId={selectedReviewId}
        onSelectedReviewChange={onSelectedReviewChange}
        messages={messages}
        setMessages={setMessages}
      />
    </div>
  )
}