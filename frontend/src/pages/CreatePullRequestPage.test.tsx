import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { afterEach, describe, expect, it, vi } from "vitest"

import CreatePullRequestPage from "@/pages/CreatePullRequestPage"

const repository = {
  id: 5,
  github_id: 201,
  owner: "octocat",
  name: "alpha",
  full_name: "octocat/alpha",
  is_private: false,
  pull_request_count: 2,
  open_pull_request_count: 1,
  latest_analysis_status: "completed",
}

function mockFetch(options?: { createFails?: boolean }) {
  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    if (url.includes("/api/repositories/5/branches")) {
      return Promise.resolve(
        new Response(JSON.stringify(["main", "feature/auth", "dev"]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    if (url.includes("/api/repositories/5") && init?.method === "POST") {
      const status = options?.createFails ? 502 : 201
      const body = options?.createFails
        ? { detail: "Could not create the pull request on GitHub" }
        : {
            id: 42,
            github_id: 900042,
            number: 42,
            title: "Add authentication",
            author: "octocat",
            state: "open",
            head_ref: "feature/auth",
            base_ref: "main",
            repository_id: 5,
            repository_full_name: "octocat/alpha",
          }
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    if (url.includes("/api/repositories/5")) {
      return Promise.resolve(
        new Response(JSON.stringify(repository), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    }
    return Promise.resolve(new Response(JSON.stringify({}), { status: 404 }))
  })
}

function renderPage(path = "/repositories/5/create-pr") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/repositories/:repositoryId/create-pr"
          element={<CreatePullRequestPage />}
        />
        <Route path="/pull-requests/:pullRequestId" element={<div>PR page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("CreatePullRequestPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("loads branches into the source and target dropdowns", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    const source = await screen.findByLabelText("Compare")
    expect(source).toHaveValue("")
    const options = Array.from(
      screen.getByLabelText("Base").querySelectorAll("option"),
    ).map((option) => option.textContent)
    expect(options).toEqual(["Select a base branch…", "main", "feature/auth", "dev"])
  })

  it("suggests a title from the compare branch", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    await screen.findByLabelText("Compare")

    const title = screen.getByLabelText("Title") as HTMLInputElement
    expect(title.value).toBe("")

    fireEvent.change(screen.getByLabelText("Compare"), {
      target: { value: "feature/auth" },
    })
    expect(title.value).toBe("Auth")
  })

  it("does not overwrite a manually typed title", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    await screen.findByLabelText("Compare")

    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "My custom title" },
    })
    fireEvent.change(screen.getByLabelText("Compare"), {
      target: { value: "fix/login-bug" },
    })

    expect((screen.getByLabelText("Title") as HTMLInputElement).value).toBe(
      "My custom title",
    )
  })

  it("creates a PR and navigates to its detail page", async () => {
    vi.stubGlobal("fetch", mockFetch())
    renderPage()
    await screen.findByLabelText("Compare")

    fireEvent.change(screen.getByLabelText("Compare"), {
      target: { value: "feature/auth" },
    })
    fireEvent.change(screen.getByLabelText("Base"), {
      target: { value: "main" },
    })
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Add authentication" },
    })
    fireEvent.click(
      screen.getByRole("button", { name: "Create Pull Request" }),
    )

    await waitFor(() => {
      expect(screen.getByText("PR page")).toBeInTheDocument()
    })
  })

  it("shows an error when GitHub rejects the PR", async () => {
    vi.stubGlobal("fetch", mockFetch({ createFails: true }))
    renderPage()
    await screen.findByLabelText("Compare")

    fireEvent.change(screen.getByLabelText("Compare"), {
      target: { value: "feature/auth" },
    })
    fireEvent.change(screen.getByLabelText("Base"), {
      target: { value: "main" },
    })
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Add authentication" },
    })
    fireEvent.click(
      screen.getByRole("button", { name: "Create Pull Request" }),
    )

    await waitFor(() => {
      expect(
        screen.getByText("Could not create the pull request on GitHub"),
      ).toBeInTheDocument()
    })
  })
})