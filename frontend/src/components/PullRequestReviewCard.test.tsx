import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { PullRequestReviewCard } from "@/components/PullRequestReviewCard"
import type { PullRequestSummary } from "@/lib/api"

const base: PullRequestSummary = {
  id: 1,
  github_id: 101,
  number: 42,
  title: "Add authentication to the API",
  author: "octocat",
  state: "open",
  repository_id: 1,
  repository_full_name: "octocat/hello-world",
  updated_at: null,
  latest_analysis_status: "completed",
  merge_readiness_score: 82,
  finding_count: 3,
  critical_count: 0,
  high_count: 2,
  medium_count: 1,
  low_count: 0,
  info_count: 0,
  test_count: 4,
}

function renderCard(pullRequest: PullRequestSummary) {
  return render(
    <MemoryRouter>
      <PullRequestReviewCard pullRequest={pullRequest} />
    </MemoryRouter>,
  )
}

describe("PullRequestReviewCard", () => {
  it("renders the PR header, statuses, and repository context", () => {
    renderCard(base)
    expect(screen.getByText("#42")).toBeInTheDocument()
    expect(screen.getByText("Add authentication to the API")).toBeInTheDocument()
    expect(screen.getByText("Completed")).toBeInTheDocument()
    expect(screen.getByText("Open")).toBeInTheDocument()
    expect(screen.getByText("octocat/hello-world")).toBeInTheDocument()
    expect(screen.getByText(/Author: octocat/)).toBeInTheDocument()
  })

  it("renders real severity rows from the data", () => {
    renderCard(base)
    expect(screen.getByText("2 high")).toBeInTheDocument()
    expect(screen.getByText("1 medium")).toBeInTheDocument()
  })

  it("renders the test count and Merge Readiness score", () => {
    renderCard(base)
    expect(screen.getByText("4 generated")).toBeInTheDocument()
    expect(screen.getByText("82")).toBeInTheDocument()
    expect(screen.getByText("/100")).toBeInTheDocument()
  })

  it("shows honest empty states for a PR with no analysis", () => {
    renderCard({
      ...base,
      latest_analysis_status: null,
      merge_readiness_score: null,
      finding_count: 0,
      high_count: 0,
      medium_count: 0,
      test_count: 0,
    })
    expect(screen.getByText("No findings")).toBeInTheDocument()
    expect(screen.getByText("No tests generated")).toBeInTheDocument()
    expect(screen.getByText("No score yet")).toBeInTheDocument()
    expect(screen.getByText("Queued")).toBeInTheDocument()
  })

  it("links to the PR detail page and GitHub", () => {
    renderCard(base)
    expect(
      screen.getByRole("link", { name: /Pull Request #42/ }),
    ).toHaveAttribute("href", "/pull-requests/1")
    expect(screen.getByRole("link", { name: "GitHub ↗" })).toHaveAttribute(
      "href",
      "https://github.com/octocat/hello-world/pull/42",
    )
  })
})