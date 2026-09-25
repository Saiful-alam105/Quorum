import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Button } from "@/components/ui/Button"

describe("Button", () => {
  it("renders a button with an accessible name", () => {
    render(<Button>Run analysis</Button>)
    expect(
      screen.getByRole("button", { name: "Run analysis" }),
    ).toBeInTheDocument()
  })

  it("uses button type by default", () => {
    render(<Button>Save</Button>)
    expect(screen.getByRole("button")).toHaveAttribute("type", "button")
  })

  it("respects an explicit type", () => {
    render(<Button type="submit">Submit</Button>)
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit")
  })

  it("applies variant classes", () => {
    render(<Button variant="outline">Cancel</Button>)
    expect(screen.getByRole("button")).toHaveClass("border-border")
  })
})