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
      screen.getByRole("heading", { name: "Core capabilities" }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("heading", { name: "How Quorum is built" }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("heading", { name: "Built for developers" }),
    ).toBeInTheDocument()
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
      screen.getByText("Product preview — example review outcome"),
    ).toBeInTheDocument()
    expect(screen.getByText("Pull Request #42")).toBeInTheDocument()
  })

  it("opens the mobile navigation menu", () => {
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