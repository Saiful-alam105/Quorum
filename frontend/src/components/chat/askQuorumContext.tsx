import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { useNavigate } from "react-router-dom"

type AskQuorumContextValue = {
  selectedReviewId: number | null
  setSelectedReviewId: (id: number | null) => void
  openWithReview: (reviewId: number) => void
}

const AskQuorumContext = createContext<AskQuorumContextValue | null>(null)

export function AskQuorumProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null)

  const openWithReview = useCallback(
    (reviewId: number) => {
      setSelectedReviewId(reviewId)
      navigate("/ask-quorum")
    },
    [navigate],
  )

  const value = useMemo<AskQuorumContextValue>(
    () => ({ selectedReviewId, setSelectedReviewId, openWithReview }),
    [selectedReviewId, setSelectedReviewId, openWithReview],
  )

  return (
    <AskQuorumContext.Provider value={value}>{children}</AskQuorumContext.Provider>
  )
}

export function useAskQuorum() {
  const context = useContext(AskQuorumContext)
  if (!context) {
    throw new Error("useAskQuorum must be used within AskQuorumProvider")
  }
  return context
}