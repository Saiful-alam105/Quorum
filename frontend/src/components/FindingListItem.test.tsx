import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { FindingListItem } from "@/components/FindingListItem"
import type { Finding } from "@/lib/api"

const finding: Finding = {
  id: 1,
  analysis_run_id: 1,
  rule_id: "python.security.example",
  severity: "high",
  title: "Shell injection",
  file: "app.py",
  line: 5,
  evidence: "evidence",
  explanation: "explanation",
  confidence: 0.9,
  pull_request_id: 1,
  pr_number: 42,
  pr_title: "Add authentication",
  repository_id: 1,
  repository_full_name: "octocat/hello-world",
}

describe("FindingListItem", () => {
  it("renders severity, title and file location", () => {
    render(
      <MemoryRouter>
        <FindingListItem finding={finding} />
      </MemoryRouter>,
    )
    expect(screen.getByText("High")).toBeInTheDocument()
    expect(screen.getByText("Shell injection")).toBeInTheDocument()
    expect(screen.getByText("app.py:5")).toBeInTheDocument()
  })

  it("renders the PR context link", () => {
    render(
      <MemoryRouter>
        <FindingListItem finding={finding} />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole("link", { name: "octocat/hello-world #42 · Add authentication" }),
    ).toHaveAttribute("href", "/pull-requests/1")
  })

  it("renders the file without a line when line is missing", () => {
    render(
      <MemoryRouter>
        <FindingListItem finding={{ ...finding, line: null }} />
      </MemoryRouter>,
    )
    expect(screen.getByText("app.py")).toBeInTheDocument()
  })
})