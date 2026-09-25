import { render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { Reveal } from "@/components/landing/Reveal"

function stubMatchMedia(matches: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockReturnValue({
      matches,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }),
  )
}

describe("Reveal", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders children immediately when IntersectionObserver is unavailable", () => {
    render(
      <Reveal>
        <div>revealed content</div>
      </Reveal>,
    )
    expect(screen.getByText("revealed content")).toBeInTheDocument()
  })

  it("keeps content visible without a hidden class under reduced motion", () => {
    stubMatchMedia(true)
    const { container } = render(
      <Reveal>
        <div>reduced motion content</div>
      </Reveal>,
    )
    expect(screen.getByText("reduced motion content")).toBeInTheDocument()
    expect(container.firstChild).not.toHaveClass("opacity-0")
  })
})