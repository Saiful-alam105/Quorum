import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import {
  normalizeSeverity,
  SeverityBadge,
  SeverityDot,
} from "@/components/severity"

describe("normalizeSeverity", () => {
  it("maps known severity values case-insensitively", () => {
    expect(normalizeSeverity("critical")).toBe("critical")
    expect(normalizeSeverity("HIGH")).toBe("high")
    expect(normalizeSeverity("Medium")).toBe("medium")
    expect(normalizeSeverity("low")).toBe("low")
    expect(normalizeSeverity("info")).toBe("info")
  })

  it("maps common aliases to critical", () => {
    expect(normalizeSeverity("error")).toBe("critical")
    expect(normalizeSeverity("blocker")).toBe("critical")
  })

  it("falls back to info for unknown or empty values", () => {
    expect(normalizeSeverity("warning")).toBe("info")
    expect(normalizeSeverity("")).toBe("info")
    expect(normalizeSeverity(undefined)).toBe("info")
    expect(normalizeSeverity(null)).toBe("info")
  })
})

describe("SeverityBadge", () => {
  it.each([
    ["critical", "Critical"],
    ["high", "High"],
    ["medium", "Medium"],
    ["low", "Low"],
    ["info", "Info"],
  ] as const)("renders a visible label for %s", (level, label) => {
    render(<SeverityBadge severity={level} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it("renders the label for uppercase backend values", () => {
    render(<SeverityBadge severity="CRITICAL" />)
    expect(screen.getByText("Critical")).toBeInTheDocument()
  })
})

describe("SeverityDot", () => {
  it("renders a dot span", () => {
    const { container } = render(<SeverityDot severity="high" />)
    expect(container.querySelector("span")).toBeInTheDocument()
  })
})