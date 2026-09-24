import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { CoverageBlock } from "@/components/CoverageBlock"
import type { CoverageResult } from "@/lib/api"

const coverage: CoverageResult = {
  id: 1,
  analysis_run_id: 1,
  coverage_before: 72.0,
  coverage_after: 81.0,
  coverage_delta: 9.0,
}

describe("CoverageBlock", () => {
  it("renders before, after and delta values", () => {
    render(<CoverageBlock coverage={coverage} />)
    expect(screen.getByText("Before")).toBeInTheDocument()
    expect(screen.getByText("72.0%")).toBeInTheDocument()
    expect(screen.getByText("81.0%")).toBeInTheDocument()
    expect(screen.getByText("9.0%")).toBeInTheDocument()
  })

  it("renders a not-measured state", () => {
    render(<CoverageBlock coverage={null} />)
    expect(screen.getByText("Coverage not measured")).toBeInTheDocument()
  })
})