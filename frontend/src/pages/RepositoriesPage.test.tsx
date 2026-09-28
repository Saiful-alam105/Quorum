import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import RepositoriesPage from "@/pages/RepositoriesPage"

const repositories = [
  {
    id: 5,
    github_id: 201,
    owner: "octocat",
    name: "alpha",
    full_name: "octocat/alpha",
    is_private: false,
    language: "Python",
    default_branch: "main",
    connected: true,
    pull_request_count: 3,
  },
  {
    id: null,
    github_id: 202,
    owner: "octocat",
    name: "beta",
    full_name: "octocat/beta",
    is_private: true,
    language: "TypeScript",
    default_branch: "main",
    connected: false,
    pull_request_count: 0,
  },
]

function mockFetch() {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes("/api/repositories/discover")) {
      return Promise.resolve(
        new Response(JSON.stringify(repositories), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    return Promise.resolve(
      new Response(JSON.stringify({}), { status: 404 }),
    )
  })
}

function renderPage(path = "/repositories") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/repositories" element={<RepositoriesPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RepositoriesPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders connected and needs-connection repositories", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    expect(await screen.findByText("octocat/alpha")).toBeInTheDocument()
    expect(screen.getByText("octocat/beta")).toBeInTheDocument()
    expect(screen.getAllByText("Connected").length).toBeGreaterThan(0)
    expect(
      screen.getByRole("button", { name: "Connect Repository" }),
    ).toBeInTheDocument()
  })

  it("links connected repositories into their workspace", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    expect(
      await screen.findByRole("link", { name: /octocat\/alpha/ }),
    ).toHaveAttribute("href", "/repositories/5")
  })

  it("shows a success banner after returning from GitHub", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage("/repositories?connected=1")
    expect(
      await screen.findByText("Repositories connected successfully."),
    ).toBeInTheDocument()
  })

  it("shows a failure banner after a cancelled connection", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage("/repositories?connected=0")
    expect(
      await screen.findByText(
        "Could not connect the repository. Please try again.",
      ),
    ).toBeInTheDocument()
  })
})