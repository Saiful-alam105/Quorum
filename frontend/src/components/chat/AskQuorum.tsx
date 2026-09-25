import { useLocation, useNavigate } from "react-router-dom"

import { AskQuorumButton } from "@/components/chat/AskQuorumButton"

export function AskQuorum() {
  const { pathname } = useLocation()
  const navigate = useNavigate()

  if (pathname === "/ask-quorum") {
    return null
  }

  return <AskQuorumButton onNavigate={() => navigate("/ask-quorum")} />
}