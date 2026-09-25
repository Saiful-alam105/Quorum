import { MessageSquare } from "lucide-react"

import { QuorumChat } from "@/components/chat/QuorumChat"
import { useAskQuorum } from "@/components/chat/askQuorumContext"

export default function AskQuorumPage() {
  const { selectedReviewId, setSelectedReviewId } = useAskQuorum()

  return (
    <>
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 shrink-0 text-muted-foreground" />
          <h1 className="text-2xl font-semibold tracking-tight">Ask Quorum</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask questions grounded in a specific review's analysis.
        </p>
      </div>

      <div className="mx-auto max-w-3xl">
        <div className="flex h-[32rem] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-lg">
          <QuorumChat
            selectedReviewId={selectedReviewId}
            onSelectedReviewChange={setSelectedReviewId}
          />
        </div>
      </div>
    </>
  )
}