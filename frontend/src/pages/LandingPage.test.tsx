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
  it("provides a skip-to-content link", () => {
    renderPage()
    expect(
      screen.getByRole("link", { name: "Skip to content" }),
    ).toHaveAttribute("href", "#landing-content")
  })

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
      screen.getByRole("heading", { name: "Built around the developer workflow" }),
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
    expect(screen.getAllByText("Ask Quorum").length).toBeGreaterThan(0)
    expect(screen.getAllByText("Roadmap").length).toBeGreaterThan(0)
  })

  it("renders the labeled review experience preview", () => {
    renderPage()
    expect(
      screen.getByText("One screen, everything about the Pull Request"),
    ).toBeInTheDocument()
    expect(screen.getByText("Shell command injection")).toBeInTheDocument()
    expect(
      screen.getAllByText("Analysis completed").length,
    ).toBeGreaterThan(0)
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
    expect(screen.getAllByText("01").length).toBeGreaterThan(0)
  })

  it("connects the primary CTA to the existing login route", () => {
    renderPage()
    const ctas = screen.getAllByRole("link", { name: "Continue with GitHub" })
    expect(ctas.length).toBeGreaterThan(0)
    for (const cta of ctas) {
      expect(cta).toHaveAttribute("href", "/login")
    }
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

  it("renders the why-quorum points", () => {
    renderPage()
    expect(
      screen.getByRole("heading", { name: "Built around the developer workflow" }),
    ).toBeInTheDocument()
    expect(screen.getByText("GitHub-native")).toBeInTheDocument()
    expect(screen.getByText("Evidence-based findings")).toBeInTheDocument()
  })

  it("renders the final call to action", () => {
    renderPage()
    expect(
      screen.getByRole("heading", {
        name: "Bring Quorum into your Pull Request workflow.",
      }),
    ).toBeInTheDocument()
    const ctas = screen.getAllByRole("link", { name: "Continue with GitHub" })
    expect(ctas.length).toBeGreaterThan(0)
    for (const cta of ctas) {
      expect(cta).toHaveAttribute("href", "/login")
    }
    expect(
      screen.getByRole("link", { name: "Explore the workflow" }),
    ).toHaveAttribute("href", "#how-it-works")
  })

  it("renders the how-to-use journey", () => {
    renderPage()
    expect(
      screen.getByRole("heading", {
        name: "From sign-in to insights in a few steps",
      }),
    ).toBeInTheDocument()
    expect(screen.getByText("Connect GitHub")).toBeInTheDocument()
    expect(screen.getByText("Create a Pull Request")).toBeInTheDocument()
    expect(screen.getByText("Check Review History")).toBeInTheDocument()
    expect(screen.getAllByText("Roadmap").length).toBeGreaterThan(0)
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