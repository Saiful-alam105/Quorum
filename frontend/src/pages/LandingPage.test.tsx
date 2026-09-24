import { fireEvent, render, screen, within } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it } from "vitest"

import LandingPage from "@/pages/LandingPage"

function renderPage() {
  return render(
    <MemoryRouter>
      <LandingPage />
    </MemoryRouter>,
  )
}

describe("LandingPage", () => {
  it("renders the hero headline and value proposition", () => {
    renderPage()
    expect(
      screen.getByRole("heading", {
        name: "Understand every Pull Request before you merge.",
      }),
    ).toBeInTheDocument()
  })

  it("renders navigation links and section anchors", () => {
    renderPage()
    expect(
      screen.getByRole("link", { name: "How it works" }),
    ).toHaveAttribute("href", "#how-it-works")
    expect(screen.getByRole("link", { name: "Features" })).toHaveAttribute(
      "href",
      "#features",
    )
    expect(screen.getByRole("link", { name: "Architecture" })).toHaveAttribute(
      "href",
      "#architecture",
    )
    expect(
      screen.getByRole("link", { name: "Why Quorum" }),
    ).toHaveAttribute("href", "#why-quorum")
  })

  it("renders the section headings", () => {
    renderPage()
    expect(
      screen.getByRole("heading", { name: "From Pull Request to findings" }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("heading", { name: "Everything a Pull Request review needs" }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("heading", { name: "How Quorum is built" }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("heading", { name: "Built for developers" }),
    ).toBeInTheDocument()
  })

  it("renders capability cards including the roadmap-only one", () => {
    renderPage()
    expect(
      screen.getAllByText("Security analysis").length,
    ).toBeGreaterThan(0)
    expect(
      screen.getAllByText("Merge Readiness").length,
    ).toBeGreaterThan(0)
    expect(screen.getByText("Ask Quorum")).toBeInTheDocument()
    expect(screen.getByText("Roadmap")).toBeInTheDocument()
  })

  it("renders the labeled review experience preview", () => {
    renderPage()
    expect(
      screen.getByText("One screen, everything about the Pull Request"),
    ).toBeInTheDocument()
    expect(screen.getByText("Shell command injection")).toBeInTheDocument()
    expect(
      screen.getAllByText("Product preview — example review outcome").length,
    ).toBeGreaterThan(0)
  })

  it("renders the problem section with honest pain points", () => {
    renderPage()
    expect(
      screen.getByRole("heading", {
        name: "Pull Requests deserve more than a quick look.",
      }),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Security issues slip through"),
    ).toBeInTheDocument()
  })

  it("renders the six-step pipeline in order", () => {
    renderPage()
    expect(
      screen.getByText("Quorum receives the Pull Request"),
    ).toBeInTheDocument()
    expect(screen.getByText("Changed code is extracted")).toBeInTheDocument()
    expect(screen.getByText("Context is prepared")).toBeInTheDocument()
    expect(screen.getByText("The analysis pipeline runs")).toBeInTheDocument()
    expect(screen.getByText("Merge Readiness is scored")).toBeInTheDocument()
    expect(screen.getByText("Findings are presented")).toBeInTheDocument()
    expect(screen.getByText("01")).toBeInTheDocument()
  })

  it("connects the primary CTA to the existing login route", () => {
    renderPage()
    const cta = screen.getByRole("link", { name: "Continue with GitHub" })
    expect(cta).toHaveAttribute("href", "/login")
  })

  it("renders the footer with a GitHub link", () => {
    renderPage()
    expect(screen.getByRole("link", { name: "GitHub" })).toHaveAttribute(
      "href",
      "https://github.com/Saiful-alam105/Quorum",
    )
  })

  it("shows a clearly labeled product preview", () => {
    renderPage()
    expect(
      screen.getAllByText("Product preview — example review outcome").length,
    ).toBeGreaterThan(0)
    expect(screen.getAllByText("Pull Request #42").length).toBeGreaterThan(0)
  })

  it("renders the security and testing section", () => {
    renderPage()
    expect(
      screen.getByText("Beyond a simple code review assistant"),
    ).toBeInTheDocument()
    expect(screen.getByText("Security evidence")).toBeInTheDocument()
    expect(screen.getByText("Generated tests")).toBeInTheDocument()
  })

  it("renders the architecture pipeline", () => {
    renderPage()
    expect(screen.getByText("How Quorum is built")).toBeInTheDocument()
    expect(screen.getByText("FastAPI backend")).toBeInTheDocument()
    expect(screen.getByText("Orchestrator")).toBeInTheDocument()
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument()
  })

  it("renders the mobile navigation menu", () => {
    renderPage()
    const toggle = screen.getByRole("button", {
      name: "Toggle navigation menu",
    })
    fireEvent.click(toggle)
    const mobileNav = screen.getByRole("navigation", { name: "Landing mobile" })
    expect(
      within(mobileNav).getByRole("link", { name: "How it works" }),
    ).toHaveAttribute("href", "#how-it-works")
    expect(
      within(mobileNav).getByRole("link", { name: "Sign in with GitHub" }),
    ).toHaveAttribute("href", "/login")
  })
})