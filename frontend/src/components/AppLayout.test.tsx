import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import { AppLayout } from "@/components/AppLayout"

function mockFetch() {
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
    return Promise.resolve(
      new Response(JSON.stringify({ detail: "Not authenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    )
  })
}

describe("AppLayout", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders a skip link, navigation, and the page content", async () => {
    vi.stubGlobal("fetch", mockFetch())
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<div>Home content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(
      screen.getByRole("link", { name: "Skip to content" }),
    ).toHaveAttribute("href", "#main-content")
    const homeLinks = screen.getAllByRole("link", { name: "Quorum home" })
    expect(homeLinks.length).toBeGreaterThan(0)
    for (const homeLink of homeLinks) {
      expect(homeLink).toHaveAttribute("href", "/")
    }
    expect(screen.getByRole("link", { name: "Repositories" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument()
    expect(screen.getByText("Home content")).toBeInTheDocument()
    expect(await screen.findByText("Connected")).toBeInTheDocument()
  })

  it("marks the active navigation item", () => {
    vi.stubGlobal("fetch", mockFetch())
    render(
      <MemoryRouter initialEntries={["/repositories"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="repositories" element={<div>Repos content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const active = screen.getByRole("link", { name: "Repositories" })
    expect(active.className).toContain("text-primary")
  })
})