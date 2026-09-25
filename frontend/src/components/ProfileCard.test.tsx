import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { ProfileCard } from "@/components/ProfileCard"
import type { CurrentUser } from "@/lib/api"

const user: CurrentUser = {
  github_id: 1,
  username: "octocat",
  avatar_url: "https://example.com/avatar.png",
  created_at: "2026-09-15T00:00:00",
  github_authorized: true,
}

describe("ProfileCard", () => {
  it("renders username, member-since, GitHub link and authorization", () => {
    render(
      <MemoryRouter>
        <ProfileCard user={user} />
      </MemoryRouter>,
    )
    expect(screen.getByText("octocat")).toBeInTheDocument()
    expect(screen.getByText(/Member since/)).toBeInTheDocument()
    expect(screen.getByText("GitHub App authorized")).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /https:\/\/github.com\/octocat/ }),
    ).toHaveAttribute("href", "https://github.com/octocat")
  })

  it("links to settings via Manage", () => {
    render(
      <MemoryRouter>
        <ProfileCard user={user} />
      </MemoryRouter>,
    )
    expect(screen.getByRole("link", { name: /Manage/ })).toHaveAttribute(
      "href",
      "/settings",
    )
  })

  it("shows the not-installed state when the GitHub App is not authorized", () => {
    render(
      <MemoryRouter>
        <ProfileCard user={{ ...user, github_authorized: false }} />
      </MemoryRouter>,
    )
    expect(screen.getByText("GitHub App not installed")).toBeInTheDocument()
  })
})