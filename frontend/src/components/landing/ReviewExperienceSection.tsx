import { GitPullRequestArrow } from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"
import { SeverityBadge } from "@/components/severity"
import { Badge } from "@/components/ui/Badge"

export function ReviewExperienceSection() {
  return (
    <LandingSection
      id="review-experience"
      eyebrow="The review experience"
      title="One screen, everything about the Pull Request"
    >
      <div className="mx-auto max-w-3xl">
        <div className="rounded-xl border border-border bg-card p-6 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
                <GitPullRequestArrow className="h-4 w-4" />
              </span>
              <div>
                <p className="font-medium">Pull Request #42</p>
                <p className="text-xs text-muted-foreground">
                  Add authentication to the API
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="success">Analysis completed</Badge>
              <span className="font-mono text-lg font-semibold">
                82
                <span className="text-xs text-muted-foreground">/100</span>
              </span>
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-border p-4">
              <p className="text-xs text-muted-foreground">Security findings</p>
              <ul className="mt-2 space-y-2">
                <li className="flex flex-wrap items-center gap-2">
                  <SeverityBadge severity="high" />
                  <span className="text-sm">Shell command injection</span>
                  <span className="font-mono text-xs text-muted-foreground">
                    auth/database.py:5
                  </span>
                </li>
                <li className="flex flex-wrap items-center gap-2">
                  <SeverityBadge severity="medium" />
                  <span className="text-sm">Dynamic eval of untrusted data</span>
                  <span className="font-mono text-xs text-muted-foreground">
                    auth/database.py:8
                  </span>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Tests</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  4 generated · 4 passed · sandbox executed
                </p>
              </div>
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Coverage</p>
                <p className="mt-1 font-mono text-sm">
                  72% <span className="text-muted-foreground">→</span> 81%
                  <span className="ml-1 text-success">+9%</span>
                </p>
              </div>
            </div>
          </div>
        </div>
        <p className="mt-3 text-center text-xs text-muted-foreground">
          Product preview — example review outcome
        </p>
      </div>
    </LandingSection>
  )
}