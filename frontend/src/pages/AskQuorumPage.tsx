import { MessageSquare } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function AskQuorumPage() {
  return (
    <>
      <PageHeader
        title="Ask Quorum"
        description="Ask questions grounded in a specific Quorum review."
      />
      <EmptyState
        icon={MessageSquare}
        title="Ask Quorum is not available yet"
        description="The chatbot will answer questions using a selected review's stored evidence. It is implemented in a later phase, so there is no review context to ground answers in yet."
      />
    </>
  )
}
