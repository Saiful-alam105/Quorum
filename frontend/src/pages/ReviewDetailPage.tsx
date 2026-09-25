import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ArrowLeft,
  ExternalLink,
  MessageSquare,
  ShieldCheck,
  TestTube2,
} from "lucide-react"

import { useAskQuorum } from "@/components/chat/askQuorumContext"
import { CoverageBlock } from "@/components/CoverageBlock"
import { EmptyState } from "@/components/EmptyState"
import { ErrorState } from "@/components/ErrorState"
import { MergeReadinessBlock } from "@/components/MergeReadinessBlock"
import { SecurityFindingCard } from "@/components/SecurityFindingCard"
import { SignInRequired } from "@/components/SignInRequired"
import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"
import { TestRunItem } from "@/components/TestRunItem"
import { Skeleton } from "@/components/ui/Skeleton"
import { getReview, isUnauthorized, type ReviewDetail } from "@/lib/api"
import { formatDateTime } from "@/lib/format"

type PageState =
  | { status: "loading" }
  | { status: "auth-required" }
  | { status: "error"; message: string }
  | { status: "ready"; review: ReviewDetail }

export default function ReviewDetailPage() {
  const { reviewId } = useParams<{ reviewId: string }>()
  const id = Number(reviewId)
  const { openWithReview } = useAskQuorum()
  const [state, setState] = useState<PageState>({ status: "loading" })

  const load = useCallback(() => {
    if (!reviewId || Number.isNaN(id)) {
      setState({ status: "error", message: "Invalid review id" })
      return
    }

    setState({ status: "loading" })
    getReview(id)
      .then((review) => setState({ status: "ready", review }))
      .catch((error: unknown) => {
        if (isUnauthorized(error)) {
          setState({ status: "auth-required" })
          return
        }
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Failed to load review",
        })
      })
  }, [id, reviewId])

  useEffect(() => {
    load()
  }, [load])

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-96" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
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

  const { review } = state

  return (
    <>
      <Link
        to="/reviews"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to review history
      </Link>

      <div className="mb-6 space-y-1.5">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{review.repository_full_name}</span>
          <span>/</span>
          <span className="text-foreground">pull #{review.pr_number}</span>
        </div>

        <div className="flex items-center gap-2">
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            {review.pr_title}
          </h1>
          <PrStateBadge state={review.pr_state} />
        </div>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
          <span>Author: {review.pr_author}</span>
          <span>· Run #{review.id}</span>
          <span>
            ·{" "}
            {review.completed_at
              ? `Completed ${formatDateTime(review.completed_at)}`
              : review.started_at
                ? `Started ${formatDateTime(review.started_at)}`
                : "Queued"}
          </span>
          {review.repository_full_name ? (
            <a
              href={`https://github.com/${review.repository_full_name}/pull/${review.pr_number}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 transition-colors hover:text-foreground"
            >
              GitHub
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
          <button
            type="button"
            onClick={() => openWithReview(review.id)}
            className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium transition-colors hover:bg-accent hover:text-foreground"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Ask Quorum
          </button>
        </div>
      </div>

      <div className="mb-8 grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <MergeReadinessBlock
            score={review.merge_readiness_score}
            recommendation={review.recommendation}
          />
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Analysis</p>
          <div className="mt-2">
            <AnalysisStatusBadge status={review.status} />
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Run Summary</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5 text-muted-foreground" />
              {review.finding_count} security{" "}
              {review.finding_count === 1 ? "finding" : "findings"}
            </p>
            <p>
              <TestTube2 className="mr-1 inline h-3.5 w-3.5 text-muted-foreground" />
              {review.test_count} generated{" "}
              {review.test_count === 1 ? "test" : "tests"}
            </p>
          </div>
        </div>
      </div>

      <h2 className="mb-3 mt-8 text-lg font-semibold">Security Findings</h2>
      {review.findings.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No findings detected"
          description="No security findings were produced for this analysis."
        />
      ) : (
        <ul className="space-y-3">
          {review.findings.map((finding) => (
            <SecurityFindingCard key={finding.id} finding={finding} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Generated Tests</h2>
      {review.tests.length === 0 ? (
        <EmptyState
          icon={TestTube2}
          title="No tests generated"
          description="No generated tests were run for this analysis."
        />
      ) : (
        <ul className="space-y-3">
          {review.tests.map((test) => (
            <TestRunItem key={test.id} test={test} />
          ))}
        </ul>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Coverage</h2>
      <CoverageBlock coverage={review.coverage} />
    </>
  )
}