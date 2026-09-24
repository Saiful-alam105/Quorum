import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

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
  finding_count: 2,
  test_count: 4,
}

function renderCard() {
  return render(
    <MemoryRouter>
      <ReviewCard review={review} />
    </MemoryRouter>,
  )
}

describe("ReviewCard", () => {
  it("renders the PR header, statuses, and repository context", () => {
    renderCard()
    expect(screen.getByText("#42")).toBeInTheDocument()
    expect(screen.getByText("Add authentication to the API")).toBeInTheDocument()
    expect(screen.getByText("Completed")).toBeInTheDocument()
    expect(screen.getByText("Open")).toBeInTheDocument()
    expect(screen.getByText("octocat/hello-world")).toBeInTheDocument()
    expect(screen.getByText(/Author: octocat/)).toBeInTheDocument()
  })

  it("renders the score, recommendation, and counts", () => {
    renderCard()
    expect(screen.getByText("82")).toBeInTheDocument()
    expect(screen.getByText("/100")).toBeInTheDocument()
    expect(
      screen.getByText("Approve with minor concerns"),
    ).toBeInTheDocument()
    expect(screen.getByText("2 findings")).toBeInTheDocument()
    expect(screen.getByText("4 generated")).toBeInTheDocument()
  })

  it("shows honest empty states when no analysis exists", () => {
    render(
      <MemoryRouter>
        <ReviewCard
          review={{
            ...review,
            status: "pending",
            merge_readiness_score: null,
            recommendation: null,
            finding_count: 0,
            test_count: 0,
          }}
        />
      </MemoryRouter>,
    )
    expect(screen.getByText("No score yet")).toBeInTheDocument()
    expect(screen.getByText("No findings")).toBeInTheDocument()
    expect(screen.getByText("No tests generated")).toBeInTheDocument()
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