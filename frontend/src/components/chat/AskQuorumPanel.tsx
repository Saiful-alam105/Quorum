import { useCallback, useEffect, useRef, useState } from "react"
import { Loader2, MessageSquare, Send, X } from "lucide-react"

import {
  getChatMessages,
  getReviews,
  postChatMessage,
  type ChatMessage,
  type ReviewSummary,
} from "@/lib/api"
import { cn } from "@/lib/utils"

const suggestions = [
  "What security issues were found?",
  "Why did this Pull Request get this score?",
  "What tests were generated?",
  "How did coverage change?",
]

export function AskQuorumPanel({
  open,
  onClose,
  selectedReviewId,
  onSelectedReviewChange,
}: {
  open: boolean
  onClose: () => void
  selectedReviewId: number | null
  onSelectedReviewChange: (id: number | null) => void
}) {
  const [reviews, setReviews] = useState<ReviewSummary[]>([])
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState("")
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    let active = true
    setReviewsLoading(true)
    setError(null)
    getReviews()
      .then((data) => {
        if (active) {
          setReviews(data)
          setReviewsLoading(false)
        }
      })
      .catch(() => {
        if (active) {
          setReviewsLoading(false)
          setError("Could not load your reviews.")
        }
      })
    return () => {
      active = false
    }
  }, [open])

  const loadMessages = useCallback((reviewId: number) => {
    setError(null)
    getChatMessages(reviewId)
      .then(setMessages)
      .catch(() => setError("Could not load the conversation."))
  }, [])

  useEffect(() => {
    if (selectedReviewId === null) {
      setMessages([])
      return
    }
    loadMessages(selectedReviewId)
  }, [selectedReviewId, loadMessages])

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" })
  }, [messages, sending])

  const handleSend = async () => {
    const text = question.trim()
    if (!text || selectedReviewId === null || sending) {
      return
    }
    const reviewId = selectedReviewId
    setQuestion("")
    setSending(true)
    setError(null)
    setMessages((previous) => [
      ...previous,
      {
        id: -1,
        analysis_run_id: reviewId,
        role: "user",
        message: text,
        timestamp: "",
      },
    ])
    try {
      const { answer } = await postChatMessage(reviewId, text)
      setMessages((previous) => [
        ...previous,
        {
          id: -2,
          analysis_run_id: reviewId,
          role: "assistant",
          message: answer,
          timestamp: "",
        },
      ])
    } catch {
      setError("Ask Quorum is temporarily unavailable. Please try again.")
    } finally {
      setSending(false)
    }
  }

  if (!open) {
    return null
  }

  const review = reviews.find((item) => item.id === selectedReviewId)

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
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Ask Quorum"
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border transition-colors hover:bg-accent"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {reviewsLoading ? (
        <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Loading reviews…
        </div>
      ) : (
        <>
          {reviews.length === 0 ? (
            <div className="flex-1 overflow-y-auto p-4 text-sm text-muted-foreground">
              No reviews available yet. Open a review to start asking questions.
            </div>
          ) : (
            <div className="border-b border-border p-3">
              <label
                htmlFor="ask-quorum-review"
                className="mb-1 block text-xs text-muted-foreground"
              >
                Review
              </label>
              <select
                id="ask-quorum-review"
                value={selectedReviewId ?? ""}
                onChange={(event) =>
                  onSelectedReviewChange(
                    event.target.value === "" ? null : Number(event.target.value),
                  )
                }
                className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
              >
                <option value="">Select a review…</option>
                {reviews.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.repository_full_name} #{item.pr_number}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedReviewId === null ? (
            <div className="flex-1 overflow-y-auto p-4 text-sm text-muted-foreground">
              Select a review to ask questions grounded in its analysis.
            </div>
          ) : (
            <>
              <div className="flex-1 space-y-3 overflow-y-auto p-4">
                {messages.length === 0 ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">
                      Ask about this review:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {suggestions.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => setQuestion(suggestion)}
                          className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={cn(
                        "max-w-[85%] rounded-lg border px-3 py-2 text-sm",
                        message.role === "user"
                          ? "ml-auto border-transparent bg-primary text-primary-foreground"
                          : "border-border bg-background",
                      )}
                    >
                      {message.message}
                    </div>
                  ))
                )}
                {sending ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Quorum is thinking…
                  </div>
                ) : null}
                <div ref={endRef} />
              </div>

              {error ? (
                <p className="border-t border-border px-4 py-2 text-xs text-severity-critical">
                  {error}
                </p>
              ) : null}

              <form
                className="flex items-center gap-2 border-t border-border p-3"
                onSubmit={(event) => {
                  event.preventDefault()
                  handleSend()
                }}
              >
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder={
                    review
                      ? `Ask about ${review.pr_title}`
                      : "Ask about this review"
                  }
                  aria-label="Ask Quorum question"
                  className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                />
                <button
                  type="submit"
                  aria-label="Send question"
                  disabled={sending || !question.trim()}
                  className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </>
          )}
        </>
      )}
    </div>
  )
}