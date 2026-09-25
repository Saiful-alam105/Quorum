import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { MessageSquare } from "lucide-react"

import { QuorumChat } from "@/components/chat/QuorumChat"
import { useAskQuorum } from "@/components/chat/askQuorumContext"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import { getCurrentUser } from "@/lib/api"

type AuthState = "loading" | "anonymous" | "authenticated"

export default function AskQuorumPage() {
  const { selectedReviewId, setSelectedReviewId, messages, setMessages } =
    useAskQuorum()
  const [searchParams] = useSearchParams()
  const [auth, setAuth] = useState<AuthState>("loading")

  useEffect(() => {
    const raw = searchParams.get("review")
    if (raw && /^\d+$/.test(raw)) {
      setSelectedReviewId(Number(raw))
    }
  }, [searchParams, setSelectedReviewId])

  useEffect(() => {
    getCurrentUser()
      .then(() => setAuth("authenticated"))
      .catch(() => setAuth("anonymous"))
  }, [])

  if (auth === "loading") {
    return <Skeleton className="h-[32rem]" />
  }

  if (auth === "anonymous") {
    return <SignInRequired />
  }

  return (
    <>
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 shrink-0 text-muted-foreground" />
          <h1 className="text-2xl font-semibold tracking-tight">Ask Quorum</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask questions about your repositories, Pull Requests, analysis results,
          and findings.
        </p>
      </div>

      <div className="mx-auto max-w-3xl">
        <div className="flex h-[32rem] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-lg">
          <QuorumChat
            selectedReviewId={selectedReviewId}
            onSelectedReviewChange={setSelectedReviewId}
            messages={messages}
            setMessages={setMessages}
          />
        </div>
      </div>
    </>
  )
}