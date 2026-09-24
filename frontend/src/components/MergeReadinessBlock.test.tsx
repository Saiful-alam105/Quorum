import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import {
  MergeReadinessBlock,
  recommendationClass,
} from "@/components/MergeReadinessBlock"

describe("recommendationClass", () => {
  it("maps score bands to colors", () => {
    expect(recommendationClass(95)).toContain("text-success")
    expect(recommendationClass(70)).toContain("text-success")
    expect(recommendationClass(60)).toContain("text-warning")
    expect(recommendationClass(30)).toContain("text-severity-critical")
  })
})

describe("MergeReadinessBlock", () => {
  it("renders the score and recommendation", () => {
    render(
      <MergeReadinessBlock score={82} recommendation="Approve with minor concerns" />,
    )
    expect(screen.getByText("82")).toBeInTheDocument()
    expect(screen.getByText("/100")).toBeInTheDocument()
    expect(
      screen.getByText("Approve with minor concerns"),
    ).toBeInTheDocument()
  })

  it("renders a no-score state", () => {
    render(<MergeReadinessBlock score={null} recommendation={null} />)
    expect(screen.getByText("No score yet")).toBeInTheDocument()
    expect(screen.queryByText("/100")).not.toBeInTheDocument()
  })
})