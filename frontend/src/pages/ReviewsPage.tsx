import { useCallback, useEffect, useState } from "react"
import { ClipboardCheck } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { ReviewCard } from "@/components/ReviewCard"
import { SignInRequired } from "@/components/SignInRequired"
import { Skeleton } from "@/components/ui/Skeleton"
import { getReviews, isUnauthorized, type ReviewSummary } from "@/lib/api"

type ReviewsState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; reviews: ReviewSummary[] }

export default function ReviewsPage() {
  const [state, setState] = useState<ReviewsState>({ status: "loading" })

  const load = useCallback(() => {
    setState({ status: "loading" })
    getReviews()
      .then((reviews) => setState({ status: "ready", reviews }))
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          setState({ status: "auth-required" })
          return
        }
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Failed to load reviews",
        })
      })
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-16" />
          ))}
        </div>
      </div>
    )
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={load} />
  }

  if (state.status === "auth-required") {
    return <SignInRequired />
  }

  const { reviews } = state

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Reviews</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Quorum analysis runs and Merge Readiness Scores.
        </p>
      </div>

      {reviews.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="No reviews yet"
          description="Completed Quorum analyses will appear here with their Merge Readiness Scores."
        />
      ) : (
        <ul className="space-y-3">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </ul>
      )}
    </>
  )
}