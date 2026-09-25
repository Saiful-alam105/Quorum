import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { AskQuorum } from "@/components/chat/AskQuorum"

describe("AskQuorum", () => {
  it("renders a closed button with an accessible label", () => {
    render(<AskQuorum />)
    const button = screen.getByRole("button", { name: "Ask Quorum" })
    expect(button).toHaveAttribute("aria-expanded", "false")
    expect(screen.queryByRole("dialog", { name: "Ask Quorum" })).not.toBeInTheDocument()
  })

  it("opens the panel on toggle and closes it", () => {
    render(<AskQuorum />)
    const button = screen.getByRole("button", { name: "Ask Quorum" })

    fireEvent.click(button)
    expect(button).toHaveAttribute("aria-expanded", "true")
    expect(
      screen.getByRole("dialog", { name: "Ask Quorum" }),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "Close Ask Quorum" }))
    expect(screen.queryByRole("dialog", { name: "Ask Quorum" })).not.toBeInTheDocument()
  })

  it("closes the panel with Escape", () => {
    render(<AskQuorum />)
    fireEvent.click(screen.getByRole("button", { name: "Ask Quorum" }))
    expect(
      screen.getByRole("dialog", { name: "Ask Quorum" }),
    ).toBeInTheDocument()

    fireEvent.keyDown(document, { key: "Escape" })
    expect(screen.queryByRole("dialog", { name: "Ask Quorum" })).not.toBeInTheDocument()
  })
})