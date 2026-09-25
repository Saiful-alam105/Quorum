import { fireEvent, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { AskQuorum } from "@/components/chat/AskQuorum"
import { AskQuorumProvider } from "@/components/chat/askQuorumContext"

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AskQuorumProvider>
        <Routes>
          <Route path="/" element={<div>Dashboard home</div>} />
          <Route path="/ask-quorum" element={<div>Ask Quorum page</div>} />
        </Routes>
        <AskQuorum />
      </AskQuorumProvider>
    </MemoryRouter>,
  )
}

describe("AskQuorum", () => {
  it("renders a closed launcher on dashboard pages", () => {
    renderAt("/")
    const button = screen.getByRole("button", { name: "Ask Quorum" })
    expect(button).toHaveAttribute("aria-expanded", "false")
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("toggles the floating chat panel", () => {
    renderAt("/")
    fireEvent.click(screen.getByRole("button", { name: "Ask Quorum" }))
    expect(
      screen.getByRole("dialog", { name: "Ask Quorum" }),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Close Ask Quorum" }))
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("opens the full Ask Quorum page from the panel", () => {
    renderAt("/")
    fireEvent.click(screen.getByRole("button", { name: "Ask Quorum" }))
    fireEvent.click(
      screen.getByRole("button", { name: "Open Ask Quorum in full page" }),
    )
    expect(screen.getByText("Ask Quorum page")).toBeInTheDocument()
    expect(
      screen.queryByRole("dialog", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
  })

  it("is hidden on the /ask-quorum page", () => {
    renderAt("/ask-quorum")
    expect(
      screen.queryByRole("button", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
    expect(screen.getByText("Ask Quorum page")).toBeInTheDocument()
  })
})