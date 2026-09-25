import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react"

import type { ChatMessage } from "@/lib/api"

type AskQuorumContextValue = {
  open: boolean
  selectedReviewId: number | null
  setSelectedReviewId: (id: number | null) => void
  messages: ChatMessage[]
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
  openWithReview: (reviewId: number) => void
  openPanel: () => void
  closePanel: () => void
  togglePanel: () => void
}

const AskQuorumContext = createContext<AskQuorumContextValue | null>(null)

export function AskQuorumProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const openWithReview = useCallback((reviewId: number) => {
    setSelectedReviewId(reviewId)
    setOpen(true)
  }, [])

  const openPanel = useCallback(() => setOpen(true), [])
  const closePanel = useCallback(() => setOpen(false), [])
  const togglePanel = useCallback(() => setOpen((value) => !value), [])

  const value = useMemo<AskQuorumContextValue>(
    () => ({
      open,
      selectedReviewId,
      setSelectedReviewId,
      messages,
      setMessages,
      openWithReview,
      openPanel,
      closePanel,
      togglePanel,
    }),
    [open, selectedReviewId, setSelectedReviewId, messages, setMessages, openWithReview, openPanel, closePanel, togglePanel],
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