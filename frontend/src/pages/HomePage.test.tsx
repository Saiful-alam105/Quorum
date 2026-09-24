import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import HomePage from "@/pages/HomePage"

function mockFetch(options: { authMe: number }) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("/health")) {
      return Promise.resolve(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    if (url.includes("/auth/me")) {
      return Promise.resolve(
        new Response(
          JSON.stringify(
            options.authMe === 200
              ? { github_id: 1, username: "octocat" }
              : { detail: "Not authenticated" },
          ),
          { status: options.authMe, headers: { "Content-Type": "application/json" } },
        ),
      )
    }
    return Promise.resolve(
      new Response(JSON.stringify({ detail: "Forbidden" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }),
    )
  })
}

describe("HomePage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("shows the landing page when not authenticated", async () => {
    vi.stubGlobal("fetch", mockFetch({ authMe: 401 }))
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    )
    expect(
      await screen.findByRole("heading", {
        name: "AI-powered Pull Request review for developers.",
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: "Continue with GitHub" }),
    ).toHaveAttribute("href", "/login")
  })

  it("shows the dashboard shell when authenticated", async () => {
    vi.stubGlobal("fetch", mockFetch({ authMe: 200 }))
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    )
    expect(
      await screen.findByRole("link", { name: "Repositories" }),
    ).toBeInTheDocument()
  })
})