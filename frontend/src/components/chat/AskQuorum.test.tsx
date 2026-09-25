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
  it("renders the launcher with an accessible label on dashboard pages", () => {
    renderAt("/")
    const button = screen.getByRole("button", { name: "Ask Quorum" })
    expect(button).toBeInTheDocument()
    expect(screen.getByText("Dashboard home")).toBeInTheDocument()
  })

  it("navigates to /ask-quorum when clicked", () => {
    renderAt("/")
    fireEvent.click(screen.getByRole("button", { name: "Ask Quorum" }))
    expect(screen.getByText("Ask Quorum page")).toBeInTheDocument()
  })

  it("is hidden on the /ask-quorum page", () => {
    renderAt("/ask-quorum")
    expect(
      screen.queryByRole("button", { name: "Ask Quorum" }),
    ).not.toBeInTheDocument()
    expect(screen.getByText("Ask Quorum page")).toBeInTheDocument()
  })
})