import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { RepositoryListItem } from "@/components/RepositoryListItem"
import type { Repository } from "@/lib/api"

const repository: Repository = {
  id: 1,
  github_id: 201,
  owner: "octocat",
  name: "hello-world",
  full_name: "octocat/hello-world",
  is_private: true,
  pull_request_count: 5,
  open_pull_request_count: 3,
  latest_analysis_status: "completed",
}

describe("RepositoryListItem", () => {
  it("renders the repository name and counts", () => {
    render(
      <MemoryRouter>
        <RepositoryListItem repository={repository} />
      </MemoryRouter>,
    )
    expect(screen.getByText("octocat/hello-world")).toBeInTheDocument()
    expect(
      screen.getByText("5 pull requests · 3 open"),
    ).toBeInTheDocument()
  })

  it("uses singular text for a single pull request", () => {
    render(
      <MemoryRouter>
        <RepositoryListItem
          repository={{ ...repository, pull_request_count: 1 }}
        />
      </MemoryRouter>,
    )
    expect(screen.getByText("1 pull request · 3 open")).toBeInTheDocument()
  })

  it("renders the private badge", () => {
    render(
      <MemoryRouter>
        <RepositoryListItem repository={repository} />
      </MemoryRouter>,
    )
    expect(screen.getByText("Private")).toBeInTheDocument()
  })

  it("renders the latest analysis status", () => {
    render(
      <MemoryRouter>
        <RepositoryListItem repository={repository} />
      </MemoryRouter>,
    )
    expect(screen.getByText("Completed")).toBeInTheDocument()
  })

  it("links to the repository detail and GitHub", () => {
    render(
      <MemoryRouter>
        <RepositoryListItem repository={repository} />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole("link", { name: /octocat\/hello-world/ }),
    ).toHaveAttribute("href", "/repositories/1")
    expect(screen.getByRole("link", { name: /GitHub/ })).toHaveAttribute(
      "href",
      "https://github.com/octocat/hello-world",
    )
  })
})