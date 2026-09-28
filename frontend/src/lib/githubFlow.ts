const POPUP_FEATURES = "width=720,height=800,resizable=yes,scrollbars=yes"

const POLL_MS = 500
const MAX_MS = 3 * 60 * 1000

/**
 * Open the GitHub App flow (install/update) in a new window, like Google's
 * account chooser. The Quorum page stays open; when the flow returns to
 * `/repositories?connected=...` or `?disconnected=...`, the popup is closed
 * and the current tab is navigated to the result so the banner appears.
 *
 * Falls back to same-tab navigation when popups are blocked.
 */
export function openGithubFlow(url: string): void {
  const popup = window.open(url, "quorum-github-flow", POPUP_FEATURES)
  if (!popup) {
    window.location.href = url
    return
  }
  watchGithubFlow(popup)
}

export function watchGithubFlow(
  popup: Window | null,
  pollMs: number = POLL_MS,
  maxMs: number = MAX_MS,
): void {
  if (!popup) {
    return
  }
  const startedAt = Date.now()
  const timer = window.setInterval(() => {
    if (Date.now() - startedAt > maxMs) {
      window.clearInterval(timer)
      if (!popup.closed) {
        popup.close()
      }
      return
    }
    if (popup.closed) {
      window.clearInterval(timer)
      return
    }

    let href: string
    try {
      href = popup.location.href
    } catch {
      // Still on a different origin (github.com) — keep polling.
      return
    }

    if (href.includes("/login")) {
      window.clearInterval(timer)
      if (!popup.closed) {
        popup.close()
      }
      window.location.href = "/login"
      return
    }

    if (!href.includes("/repositories?")) {
      return
    }

    window.clearInterval(timer)
    if (!popup.closed) {
      popup.close()
    }
    try {
      const params = new URL(href).searchParams
      const connected = params.get("connected")
      const disconnected = params.get("disconnected")
      const result =
        connected !== null
          ? `connected=${connected}`
          : `disconnected=${disconnected}`
      window.location.href = `/repositories?${result}`
    } catch {
      window.location.href = "/repositories"
    }
  }, pollMs)
}