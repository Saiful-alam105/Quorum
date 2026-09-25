import { CheckCircle2 } from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"

const points = [
  {
    title: "GitHub-native",
    description:
      "Webhooks and the GitHub API keep Quorum inside the workflow developers already use.",
  },
  {
    title: "Evidence-based findings",
    description:
      "Security and test results are grounded in measured, verifiable evidence.",
  },
  {
    title: "Testing assistance",
    description:
      "Generated tests run in an isolated sandbox with coverage measured before and after.",
  },
  {
    title: "Structured findings",
    description:
      "Severity, file, and line information make findings easy to act on.",
  },
  {
    title: "Context-aware analysis",
    description:
      "Bounded context keeps analysis focused on the relevant changed code.",
  },
  {
    title: "A central dashboard",
    description:
      "Repositories, Pull Requests, reviews, and findings in one place.",
  },
]

export function WhyQuorumSection() {
  return (
    <LandingSection
      id="why-quorum"
      eyebrow="Why Quorum"
      title="Built around the developer workflow"
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {points.map((point) => (
          <div key={point.title} className="card-lift rounded-lg border border-border bg-card p-5">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
              <div>
                <h3 className="font-semibold">{point.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {point.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </LandingSection>
  )
}