import { useEffect } from "react"

import { AskQuorumButton } from "@/components/chat/AskQuorumButton"
import { AskQuorumPanel } from "@/components/chat/AskQuorumPanel"
import { useAskQuorum } from "@/components/chat/askQuorumContext"

export function AskQuorum() {
  const { open, togglePanel, closePanel, selectedReviewId, setSelectedReviewId } =
    useAskQuorum()

  useEffect(() => {
    if (!open) {
      return
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closePanel()
      }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [open, closePanel])

  return (
    <>
      <AskQuorumPanel
        open={open}
        onClose={closePanel}
        selectedReviewId={selectedReviewId}
        onSelectedReviewChange={setSelectedReviewId}
      />
      <AskQuorumButton open={open} onToggle={togglePanel} />
    </>
  )
}