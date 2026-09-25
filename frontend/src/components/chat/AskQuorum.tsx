import { useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"

import { AskQuorumButton } from "@/components/chat/AskQuorumButton"
import { AskQuorumPanel } from "@/components/chat/AskQuorumPanel"
import { useAskQuorum } from "@/components/chat/askQuorumContext"

export function AskQuorum() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { open, togglePanel, closePanel, selectedReviewId, setSelectedReviewId, messages, setMessages } =
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

  if (pathname === "/ask-quorum") {
    return null
  }

  const openFullPage = () => {
    closePanel()
    const target =
      selectedReviewId != null
        ? `/ask-quorum?review=${selectedReviewId}`
        : "/ask-quorum"
    navigate(target)
  }

  return (
    <>
      <AskQuorumPanel
        open={open}
        onClose={closePanel}
        onOpenPage={openFullPage}
        selectedReviewId={selectedReviewId}
        onSelectedReviewChange={setSelectedReviewId}
        messages={messages}
        setMessages={setMessages}
      />
      <AskQuorumButton open={open} onToggle={togglePanel} />
    </>
  )
}