import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import { AskQuorumProvider } from "@/components/chat/askQuorumContext"
import AskQuorumPage from "@/pages/AskQuorumPage"

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

function mockFetch(options?: { authMe?: number }) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("/auth/me")) {
      return Promise.resolve(
        new Response(
          JSON.stringify(
            options?.authMe === 401
              ? { detail: "Not authenticated" }
              : { github_id: 1, username: "octocat" },
          ),
          { status: options?.authMe ?? 200, headers: { "Content-Type": "application/json" } },
        ),
      )
    }
    if (url.endsWith("/chat")) {
      return Promise.resolve(
        new Response("[]", {
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

describe("AskQuorumPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders the page header and the review selector", async () => {
    vi.stubGlobal("fetch", mockFetch())
    render(
      <MemoryRouter>
        <AskQuorumProvider>
          <AskQuorumPage />
        </AskQuorumProvider>
      </MemoryRouter>,
    )

    expect(
      await screen.findByRole("heading", { name: "Ask Quorum" }),
    ).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByLabelText("Review")).toBeInTheDocument()
    })
    expect(screen.getByText("octocat/hello-world #42")).toBeInTheDocument()
  })

  it("pre-selects the review from the query param", async () => {
    vi.stubGlobal("fetch", mockFetch())
    render(
      <MemoryRouter initialEntries={["/ask-quorum?review=5"]}>
        <AskQuorumProvider>
          <AskQuorumPage />
        </AskQuorumProvider>
      </MemoryRouter>,
    )

    expect(
      await screen.findByRole("heading", { name: "Ask Quorum" }),
    ).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByLabelText("Review")).toHaveValue("5")
    })
    await waitFor(() => {
      expect(screen.getByLabelText("Ask Quorum question")).toBeInTheDocument()
    })
  })

  it("shows the sign-in required state for unauthenticated visitors", async () => {
    vi.stubGlobal("fetch", mockFetch({ authMe: 401 }))
    render(
      <MemoryRouter>
        <AskQuorumProvider>
          <AskQuorumPage />
        </AskQuorumProvider>
      </MemoryRouter>,
    )

    expect(
      await screen.findByRole("heading", { name: "Sign in required" }),
    ).toBeInTheDocument()
  })
})