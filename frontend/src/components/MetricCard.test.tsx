import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { FolderGit2 } from "lucide-react"

import { MetricCard } from "@/components/MetricCard"

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="Repositories" value={4} icon={FolderGit2} />)
    expect(screen.getByText("Repositories")).toBeInTheDocument()
    expect(screen.getByText("4")).toBeInTheDocument()
  })

  it("renders an optional hint", () => {
    render(
      <MetricCard label="Findings" value={2} icon={FolderGit2} hint="from latest runs" />,
    )
    expect(screen.getByText("from latest runs")).toBeInTheDocument()
  })

  it("applies the critical accent", () => {
    render(
      <MetricCard label="Critical" value={1} icon={FolderGit2} accent="critical" />,
    )
    const iconContainer = screen.getByText("Critical").nextElementSibling
    expect(iconContainer).toHaveClass("bg-severity-critical/15")
  })
})