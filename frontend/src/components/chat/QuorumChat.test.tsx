import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { QuorumChat } from "@/components/chat/QuorumChat"

const reviews = [
  {
    id: 5,
    pull_request_id: 1,
    pr_number: 42,
    pr_title: "Add authentication",
    pr_author: "octocat",
    pr_state: "open",
    repository_id: 1,
    repository_full_name: "octocat/hello-world",
    status: "completed",
    merge_readiness_score: 82,
    recommendation: "Approve with minor concerns",
    started_at: null,
    completed_at: null,
    finding_count: 2,
    critical_count: 0,
    high_count: 1,
    medium_count: 1,
    low_count: 0,
    info_count: 0,
    test_count: 4,
    coverage_before: 72,
    coverage_after: 81,
    coverage_delta: 9,
  },
]

function mockFetch(options: { chat?: unknown[]; answer?: string }) {
  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith("/chat")) {
      if (init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ answer: options.answer ?? "answer text" }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        )
      }
      return Promise.resolve(
        new Response(JSON.stringify(options.chat ?? []), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    if (url.includes("/api/reviews")) {
      return Promise.resolve(
        new Response(JSON.stringify(reviews), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
  })
}

function renderChat(selectedReviewId: number | null) {
  return render(
    <QuorumChat
      selectedReviewId={selectedReviewId}
      onSelectedReviewChange={() => {}}
    />,
  )
}

describe("QuorumChat", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("shows suggestions when a review is selected", async () => {
    vi.stubGlobal("fetch", mockFetch({}))
    renderChat(5)
    await waitFor(() => {
      expect(
        screen.getByText("What security issues were found?"),
      ).toBeInTheDocument()
    })
  })

  it("shows the selected review in a context bar", async () => {
    vi.stubGlobal("fetch", mockFetch({}))
    renderChat(5)
    await waitFor(() => {
      expect(screen.getByText(/Answering about/)).toBeInTheDocument()
    })
    expect(
      screen.getAllByText(/octocat\/hello-world #42/).length,
    ).toBeGreaterThan(0)
  })

  it("sends a question and renders the answer", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({ answer: "The review found 2 security issues." }),
    )
    renderChat(5)
    await waitFor(() => {
      expect(screen.getByLabelText("Ask Quorum question")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText("Ask Quorum question"), {
      target: { value: "What did you find?" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Send question" }))

    await waitFor(() => {
      expect(
        screen.getByText("The review found 2 security issues."),
      ).toBeInTheDocument()
    })
    expect(screen.getByText("What did you find?")).toBeInTheDocument()
  })
})