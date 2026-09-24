import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { SecurityFindingCard } from "@/components/SecurityFindingCard"
import type { SecurityFinding } from "@/lib/api"

const finding: SecurityFinding = {
  id: 1,
  analysis_run_id: 1,
  rule_id: "python.security.example",
  severity: "high",
  title: "Shell injection",
  file: "app.py",
  line: 5,
  evidence: "subprocess.call(cmd, shell=True)",
  explanation: "Use shell=False to avoid command injection.",
  confidence: 0.9,
}

describe("SecurityFindingCard", () => {
  it("renders severity, title and file location", () => {
    render(<SecurityFindingCard finding={finding} />)
    expect(screen.getByText("High")).toBeInTheDocument()
    expect(screen.getByText("Shell injection")).toBeInTheDocument()
    expect(
      screen.getByText("app.py:5 · python.security.example"),
    ).toBeInTheDocument()
  })

  it("renders evidence and explanation", () => {
    render(<SecurityFindingCard finding={finding} />)
    expect(
      screen.getByText("subprocess.call(cmd, shell=True)"),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Use shell=False to avoid command injection."),
    ).toBeInTheDocument()
  })

  it("omits evidence when absent", () => {
    render(
      <SecurityFindingCard finding={{ ...finding, evidence: "", explanation: null }} />,
    )
    expect(
      screen.queryByText("subprocess.call(cmd, shell=True)"),
    ).not.toBeInTheDocument()
  })
})