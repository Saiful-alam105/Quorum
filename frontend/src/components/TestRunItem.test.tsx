import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { TestRunItem } from "@/components/TestRunItem"
import type { TestRun } from "@/lib/api"

const test: TestRun = {
  id: 1,
  analysis_run_id: 1,
  test_name: "test_invalid_password",
  status: "failed",
  duration: 0.42,
  stdout: null,
  stderr: "AssertionError: expected True to be False",
  failure_reason: "assertion failed",
}

describe("TestRunItem", () => {
  it("renders the test name and status", () => {
    render(<TestRunItem test={test} />)
    expect(screen.getByText("test_invalid_password")).toBeInTheDocument()
    expect(screen.getByText("failed")).toBeInTheDocument()
  })

  it("renders duration and failure reason", () => {
    render(<TestRunItem test={test} />)
    expect(screen.getByText("Duration: 0.42s")).toBeInTheDocument()
    expect(screen.getByText("assertion failed")).toBeInTheDocument()
  })

  it("capitalizes the status", () => {
    render(<TestRunItem test={{ ...test, status: "passed" }} />)
    expect(screen.getByText("passed")).toBeInTheDocument()
  })

  it("hides optional sections when absent", () => {
    render(
      <TestRunItem
        test={{ ...test, duration: null, failure_reason: null, stderr: null }}
      />,
    )
    expect(screen.queryByText("Duration: 0.42s")).not.toBeInTheDocument()
    expect(screen.queryByText("assertion failed")).not.toBeInTheDocument()
  })
})