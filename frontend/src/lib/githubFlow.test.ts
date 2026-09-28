import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { openGithubFlow, watchGithubFlow } from "@/lib/githubFlow"

function createFakePopup(href: string): {
  closed: boolean
  location: { href: string }
  close: () => void
} {
  return {
    closed: false,
    location: { href },
    close() {
      this.closed = true
    },
  }
}

function stubWindowLocation(hrefSetter: (value: string) => void) {
  Object.defineProperty(window, "location", {
    configurable: true,
    value: {
      get href() {
        return ""
      },
      set href(value: string) {
        hrefSetter(value)
      },
    },
  })
}

describe("githubFlow", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it("falls back to same-tab navigation when the popup is blocked", () => {
    vi.spyOn(window, "open").mockReturnValue(null)
    const setter = vi.fn()
    stubWindowLocation(setter)

    openGithubFlow("https://github.com/apps/quorum/installations/new")
    expect(setter).toHaveBeenCalledWith(
      "https://github.com/apps/quorum/installations/new",
    )
  })

  it("navigates to the connected result when the popup returns", () => {
    const popup = createFakePopup("https://github.com/apps/quorum/installations/new")
    vi.spyOn(window, "open").mockReturnValue(popup as unknown as Window)
    const setter = vi.fn()
    stubWindowLocation(setter)

    openGithubFlow("https://github.com/apps/quorum/installations/new")
    popup.location.href = "http://localhost:5173/repositories?connected=1"
    vi.advanceTimersByTime(600)

    expect(popup.closed).toBe(true)
    expect(setter).toHaveBeenCalledWith("/repositories?connected=1")
  })

  it("navigates to the disconnected result when the popup returns", () => {
    const popup = createFakePopup("https://github.com/settings/installations/555")
    vi.spyOn(window, "open").mockReturnValue(popup as unknown as Window)
    const setter = vi.fn()
    stubWindowLocation(setter)

    openGithubFlow("https://github.com/settings/installations/555")
    popup.location.href = "http://localhost:5173/repositories?disconnected=1"
    vi.advanceTimersByTime(600)

    expect(popup.closed).toBe(true)
    expect(setter).toHaveBeenCalledWith("/repositories?disconnected=1")
  })

  it("ignores cross-origin popup pages until it returns to Quorum", () => {
    const popup = {
      closed: false,
      location: {
        get href() {
          throw new Error("cross-origin")
        },
      },
      close() {
        this.closed = true
      },
    }
    const setter = vi.fn()
    stubWindowLocation(setter)
    vi.spyOn(window, "open").mockReturnValue(popup as unknown as Window)

    openGithubFlow("https://github.com/apps/quorum/installations/new")
    vi.advanceTimersByTime(1500)
    expect(popup.closed).toBe(false)
    expect(setter).not.toHaveBeenCalled()
  })

  it("routes to login when the flow lands there", () => {
    const popup = createFakePopup("https://github.com/apps/quorum/installations/new")
    vi.spyOn(window, "open").mockReturnValue(popup as unknown as Window)
    const setter = vi.fn()
    stubWindowLocation(setter)

    openGithubFlow("https://github.com/apps/quorum/installations/new")
    popup.location.href = "http://localhost:5173/login"
    vi.advanceTimersByTime(600)

    expect(popup.closed).toBe(true)
    expect(setter).toHaveBeenCalledWith("/login")
  })

  it("gives up after the timeout", () => {
    const popup = createFakePopup("https://github.com/apps/quorum/installations/new")
    const setter = vi.fn()
    stubWindowLocation(setter)

    watchGithubFlow(popup as unknown as Window, 500, 2000)
    vi.advanceTimersByTime(2500)
    expect(popup.closed).toBe(true)
    expect(setter).not.toHaveBeenCalled()
  })
})