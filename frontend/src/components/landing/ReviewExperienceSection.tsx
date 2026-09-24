import { ClipboardCheck } from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"
import { AnalysisStatusBadge, PrStateBadge } from "@/components/status"

export function ReviewExperienceSection() {
  return (
    <LandingSection
      id="review-experience"
      eyebrow="The review experience"
      title="One screen, everything about the Pull Request"
    >
      <div className="mx-auto max-w-3xl">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
                <ClipboardCheck className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-medium">
                  Pull Request{" "}
                  <span className="text-muted-foreground">#42</span>
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  Add authentication to the API
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <AnalysisStatusBadge status="completed" />
              <PrStateBadge state="open" />
            </div>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-border p-4">
              <p className="text-xs text-muted-foreground">Merge Readiness</p>
              <p className="mt-2 font-mono text-2xl font-semibold">
                82
                <span className="text-xs text-muted-foreground">/100</span>
              </p>
              <p className="mt-1 text-xs font-medium text-success">
                Approve with minor concerns
              </p>
            </div>
            <div className="rounded-lg border border-border p-4">
              <p className="text-xs text-muted-foreground">Security</p>
              <p className="mt-2 text-sm text-muted-foreground">2 findings</p>
            </div>
            <div className="rounded-lg border border-border p-4">
              <p className="text-xs text-muted-foreground">Tests</p>
              <p className="mt-2 text-sm text-muted-foreground">4 generated</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-border pt-3 text-xs text-muted-foreground">
            <span>octocat/hello-world</span>
            <span>· Author: octocat</span>
            <span>· Sep 22, 2026</span>
          </div>
        </div>
        <p className="mt-3 text-center text-xs text-muted-foreground">
          Product preview — example review outcome
        </p>
      </div>
    </LandingSection>
  )
}