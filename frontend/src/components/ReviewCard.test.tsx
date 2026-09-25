import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { AskQuorumProvider } from "@/components/chat/askQuorumContext"
import { ReviewCard } from "@/components/ReviewCard"
import type { ReviewSummary } from "@/lib/api"

const review: ReviewSummary = {
  id: 5,
  pull_request_id: 1,
  pr_number: 42,
  pr_title: "Add authentication to the API",
  pr_author: "octocat",
  pr_state: "open",
  repository_id: 1,
  repository_full_name: "octocat/hello-world",
  status: "completed",
  merge_readiness_score: 82,
  recommendation: "Approve with minor concerns",
  started_at: null,
  completed_at: "2026-09-22T03:00:51.170139",
  finding_count: 3,
  critical_count: 1,
  high_count: 1,
  medium_count: 1,
  low_count: 0,
  info_count: 0,
  test_count: 4,
  coverage_before: 72.0,
  coverage_after: 81.0,
  coverage_delta: 9.0,
}

function renderCard() {
  return render(
    <AskQuorumProvider>
      <MemoryRouter>
        <ReviewCard review={review} />
      </MemoryRouter>
    </AskQuorumProvider>,
  )
}

describe("ReviewCard", () => {
  it("renders the PR header, status, score, and repository context", () => {
    renderCard()
    expect(screen.getByText("#42")).toBeInTheDocument()
    expect(screen.getByText("Add authentication to the API")).toBeInTheDocument()
    expect(screen.getByText("Completed")).toBeInTheDocument()
    expect(screen.getByText("82")).toBeInTheDocument()
    expect(screen.getByText("/100")).toBeInTheDocument()
    expect(screen.getByText("octocat/hello-world")).toBeInTheDocument()
    expect(screen.getByText(/Author: octocat/)).toBeInTheDocument()
  })

  it("renders the security breakdown, tests, and coverage", () => {
    renderCard()
    expect(screen.getByText("1 critical")).toBeInTheDocument()
    expect(screen.getByText("1 high")).toBeInTheDocument()
    expect(screen.getByText("1 medium")).toBeInTheDocument()
    expect(screen.getByText("4 generated")).toBeInTheDocument()
    expect(screen.getByText(/72%/)).toBeInTheDocument()
    expect(screen.getByText(/81%/)).toBeInTheDocument()
    expect(screen.getByText("+9%")).toBeInTheDocument()
  })

  it("shows honest empty states when no analysis exists", () => {
    render(
      <AskQuorumProvider>
        <MemoryRouter>
          <ReviewCard
            review={{
              ...review,
              status: "pending",
              merge_readiness_score: null,
              finding_count: 0,
              critical_count: 0,
              high_count: 0,
              medium_count: 0,
              test_count: 0,
              coverage_before: null,
              coverage_after: null,
              coverage_delta: null,
            }}
          />
        </MemoryRouter>
      </AskQuorumProvider>,
    )
    expect(screen.getByText("No score")).toBeInTheDocument()
    expect(screen.getByText("No findings")).toBeInTheDocument()
    expect(screen.getByText("No tests generated")).toBeInTheDocument()
    expect(screen.getByText("Not measured")).toBeInTheDocument()
    expect(screen.getByText("Queued")).toBeInTheDocument()
  })

  it("links to the review detail and GitHub", () => {
    renderCard()
    expect(
      screen.getByRole("link", { name: /Pull Request #42/ }),
    ).toHaveAttribute("href", "/reviews/5")
    expect(screen.getByRole("link", { name: "GitHub ↗" })).toHaveAttribute(
      "href",
      "https://github.com/octocat/hello-world/pull/42",
    )
  })
})