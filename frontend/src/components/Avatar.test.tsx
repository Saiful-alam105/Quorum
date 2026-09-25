import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Avatar } from "@/components/Avatar"

describe("Avatar", () => {
  it("renders the GitHub profile picture when a src is provided", () => {
    const { container } = render(
      <Avatar name="octocat" src="https://example.com/avatar.png" />,
    )
    const img = container.querySelector("img")
    expect(img).not.toBeNull()
    expect(img).toHaveAttribute("src", "https://example.com/avatar.png")
  })

  it("falls back to the initial when no profile picture exists", () => {
    render(<Avatar name="octocat" src={null} />)
    expect(screen.getByText("O")).toBeInTheDocument()
    expect(screen.queryByRole("img")).not.toBeInTheDocument()
  })

  it("falls back to a placeholder when both name and src are missing", () => {
    render(<Avatar name={null} src={null} />)
    expect(screen.getByText("?")).toBeInTheDocument()
  })
})