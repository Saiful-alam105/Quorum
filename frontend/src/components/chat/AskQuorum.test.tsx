import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import { AskQuorum } from "@/components/chat/AskQuorum"

function mockFetch(options: {
  reviews: unknown[]
  chat?: unknown[]
  answer?: string
}) {
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
        new Response(JSON.stringify(options.reviews), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
  })
}

function renderChat() {
  return render(
    <MemoryRouter>
      <AskQuorum />
    </MemoryRouter>,
  )
}

async function openPanel() {
  const button = screen.getByRole("button", { name: "Ask Quorum" })
  fireEvent.click(button)
  await waitFor(() => {
    expect(screen.getByRole("dialog", { name: "Ask Quorum" })).toBeInTheDocument()
  })
}

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

describe("AskQuorum", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders a closed button with an accessible label", () => {
    vi.stubGlobal("fetch", mockFetch({ reviews }))
    renderChat()
    const button = screen.getByRole("button", { name: "Ask Quorum" })
    expect(button).toHaveAttribute("aria-expanded", "false")
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("opens the panel and closes it", async () => {
    vi.stubGlobal("fetch", mockFetch({ reviews }))
    renderChat()
    const button = screen.getByRole("button", { name: "Ask Quorum" })

    fireEvent.click(button)
    expect(button).toHaveAttribute("aria-expanded", "true")
    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Ask Quorum" })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: "Close Ask Quorum" }))
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("closes the panel with Escape", async () => {
    vi.stubGlobal("fetch", mockFetch({ reviews }))
    renderChat()
    await openPanel()
    fireEvent.keyDown(document, { key: "Escape" })
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("shows suggestions for a selected review", async () => {
    vi.stubGlobal("fetch", mockFetch({ reviews }))
    renderChat()
    await openPanel()

    const select = screen.getByLabelText("Review")
    fireEvent.change(select, { target: { value: "5" } })

    await waitFor(() => {
      expect(
        screen.getByText("What security issues were found?"),
      ).toBeInTheDocument()
    })
  })

  it("sends a question and shows the grounded answer", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({ reviews, answer: "Two high-severity issues were found." }),
    )
    renderChat()
    await openPanel()

    const select = screen.getByLabelText("Review")
    fireEvent.change(select, { target: { value: "5" } })
    await waitFor(() => {
      expect(screen.getByLabelText("Ask Quorum question")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText("Ask Quorum question"), {
      target: { value: "What security issues were found?" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Send question" }))

    await waitFor(() => {
      expect(
        screen.getByText("Two high-severity issues were found."),
      ).toBeInTheDocument()
    })
  })

  it("shows an error when a question fails", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith("/chat")) {
        if (init?.method === "POST") {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "unavailable" }), {
              status: 503,
              headers: { "Content-Type": "application/json" },
            }),
          )
        }
        return Promise.resolve(
          new Response("[]", {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        )
      }
      return Promise.resolve(
        new Response(JSON.stringify(reviews), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    })
    vi.stubGlobal("fetch", fetchMock)
    renderChat()
    await openPanel()

    const select = screen.getByLabelText("Review")
    fireEvent.change(select, { target: { value: "5" } })
    await waitFor(() => {
      expect(screen.getByLabelText("Ask Quorum question")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText("Ask Quorum question"), {
      target: { value: "hello" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Send question" }))

    await waitFor(() => {
      expect(
        screen.getByText("Ask Quorum is temporarily unavailable. Please try again."),
      ).toBeInTheDocument()
    })
  })
})