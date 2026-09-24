import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"

describe("AnalysisStatusBadge", () => {
  it.each([
    ["pending", "Queued"],
    ["in_progress", "Running"],
    ["completed", "Completed"],
    ["failed", "Failed"],
  ] as const)("renders %s as %s", (status, label) => {
    render(<AnalysisStatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it("accepts uppercase backend values", () => {
    render(<AnalysisStatusBadge status="COMPLETED" />)
    expect(screen.getByText("Completed")).toBeInTheDocument()
  })

  it("defaults unknown statuses to Queued", () => {
    render(<AnalysisStatusBadge status="weird" />)
    expect(screen.getByText("Queued")).toBeInTheDocument()
  })

  it("defaults null status to Queued", () => {
    render(<AnalysisStatusBadge status={null} />)
    expect(screen.getByText("Queued")).toBeInTheDocument()
  })
})

describe("PrStateBadge", () => {
  it("renders Open for open state", () => {
    render(<PrStateBadge state="open" />)
    expect(screen.getByText("Open")).toBeInTheDocument()
  })

  it("renders the raw state otherwise", () => {
    render(<PrStateBadge state="merged" />)
    expect(screen.getByText("merged")).toBeInTheDocument()
  })
})