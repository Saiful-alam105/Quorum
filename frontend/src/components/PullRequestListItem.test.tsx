import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { PullRequestListItem } from "@/components/PullRequestListItem"
import type { PullRequestSummary } from "@/lib/api"

const base: PullRequestSummary = {
  id: 1,
  github_id: 101,
  number: 42,
  title: "Add authentication",
  author: "octocat",
  state: "open",
  repository_id: 1,
  repository_full_name: "octocat/hello-world",
  updated_at: null,
  latest_analysis_status: "completed",
  merge_readiness_score: 82,
  finding_count: 3,
  critical_count: 1,
  high_count: 1,
  medium_count: 1,
  low_count: 0,
  info_count: 0,
  test_count: 5,
}

function renderRow(pullRequest: PullRequestSummary) {
  return render(
    <MemoryRouter>
      <PullRequestListItem pullRequest={pullRequest} />
    </MemoryRouter>,
  )
}

describe("PullRequestListItem", () => {
  it("renders PR title, number, repository and author", () => {
    renderRow(base)
    const link = screen.getByRole("link", { name: /Add authentication/ })
    expect(link).toHaveAttribute("href", "/pull-requests/1")
    expect(link).toHaveTextContent("octocat/hello-world")
    expect(link).toHaveTextContent("#42")
    expect(screen.getByText("Author: octocat")).toBeInTheDocument()
  })

  it("renders analysis status and PR state badges", () => {
    renderRow(base)
    expect(screen.getByText("Completed")).toBeInTheDocument()
    expect(screen.getByText("Open")).toBeInTheDocument()
  })

  it("shows the finding count", () => {
    renderRow(base)
    expect(screen.getByText("3 findings")).toBeInTheDocument()
  })

  it("renders a single finding with singular text", () => {
    renderRow({ ...base, finding_count: 1, critical_count: 0 })
    expect(screen.getByText("1 finding")).toBeInTheDocument()
  })

  it("links to the GitHub pull request", () => {
    renderRow(base)
    expect(
      screen.getByRole("link", { name: "GitHub ↗" }),
    ).toHaveAttribute(
      "href",
      "https://github.com/octocat/hello-world/pull/42",
    )
  })

  it("renders queued status when no analysis exists", () => {
    renderRow({ ...base, latest_analysis_status: null, finding_count: 0 })
    expect(screen.getByText("Queued")).toBeInTheDocument()
  })
})