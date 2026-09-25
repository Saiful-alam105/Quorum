import { useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"

import { AskQuorumButton } from "@/components/chat/AskQuorumButton"
import { AskQuorumPanel } from "@/components/chat/AskQuorumPanel"
import { useAskQuorum } from "@/components/chat/askQuorumContext"

export function AskQuorum() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
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

  if (pathname === "/ask-quorum") {
    return null
  }

  const openFullPage = () => {
    closePanel()
    navigate("/ask-quorum")
  }

  return (
    <>
      <AskQuorumPanel
        open={open}
        onClose={closePanel}
        onOpenPage={openFullPage}
        selectedReviewId={selectedReviewId}
        onSelectedReviewChange={setSelectedReviewId}
      />
      <AskQuorumButton open={open} onToggle={togglePanel} />
    </>
  )
}