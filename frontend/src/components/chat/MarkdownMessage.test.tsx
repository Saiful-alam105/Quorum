import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { MarkdownMessage } from "@/components/chat/MarkdownMessage"

describe("MarkdownMessage", () => {
  it("renders headings, bullets, code spans, and bold", () => {
    render(
      <MarkdownMessage
        text={
          "### Security issues were found\n\n" +
          "- **Location:** `auth.py:5`\n" +
          "- **Problem:** `eval(data)` runs dynamic code"
        }
      />,
    )
    expect(
      screen.getByRole("heading", { name: "Security issues were found" }),
    ).toBeInTheDocument()
    expect(screen.getByText("Location:")).toBeInTheDocument()
    expect(screen.getByText("auth.py:5")).toBeInTheDocument()
    expect(screen.getByText("Problem:")).toBeInTheDocument()
    expect(screen.getByText("eval(data)")).toBeInTheDocument()
  })

  it("preserves inline code as code elements", () => {
    const { container } = render(<MarkdownMessage text={"Use `shell=False`."} />)
    expect(container.querySelector("code")).toHaveTextContent("shell=False")
  })

  it("escapes raw HTML instead of injecting it", () => {
    const { container } = render(
      <MarkdownMessage text={"<script>alert('xss')</script>safe text"} />,
    )
    expect(container.querySelector("script")).not.toBeInTheDocument()
    const text = container.textContent ?? ""
    expect(text).toContain("safe text")
    expect(text).toContain("<script>")
  })

  it("renders plain text unchanged", () => {
    render(<MarkdownMessage text={"The review found 2 issues."} />)
    expect(screen.getByText("The review found 2 issues.")).toBeInTheDocument()
  })
})