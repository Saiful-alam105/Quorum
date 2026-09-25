import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Reveal } from "@/components/landing/Reveal"

describe("Reveal", () => {
  it("renders children immediately when IntersectionObserver is unavailable", () => {
    render(
      <Reveal>
        <div>revealed content</div>
      </Reveal>,
    )
    expect(screen.getByText("revealed content")).toBeInTheDocument()
  })
})