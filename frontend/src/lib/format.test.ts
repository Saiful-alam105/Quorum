import { describe, expect, it } from "vitest"

import { formatDateTime, formatUpdatedAt } from "@/lib/format"

describe("formatUpdatedAt", () => {
  it("returns an empty string for missing or invalid values", () => {
    expect(formatUpdatedAt(null)).toBe("")
    expect(formatUpdatedAt(undefined)).toBe("")
    expect(formatUpdatedAt("not-a-date")).toBe("")
  })

  it("formats recent timestamps as relative time", () => {
    const minutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
    expect(formatUpdatedAt(minutesAgo)).toBe("5m ago")

    const hoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    expect(formatUpdatedAt(hoursAgo)).toBe("2h ago")

    const daysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    expect(formatUpdatedAt(daysAgo)).toBe("3d ago")
  })

  it("labels very recent timestamps as just now", () => {
    const now = new Date().toISOString()
    expect(formatUpdatedAt(now)).toBe("just now")
  })
})

describe("formatDateTime", () => {
  it("returns an empty string for missing values", () => {
    expect(formatDateTime(null)).toBe("")
    expect(formatDateTime("not-a-date")).toBe("")
  })

  it("formats a valid timestamp into a localized date time", () => {
    const value = "2026-09-22T03:00:51.170139"
    expect(formatDateTime(value)).not.toBe("")
  })
})