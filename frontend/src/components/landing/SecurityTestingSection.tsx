import { Fragment } from "react"
import {
  ArrowRight,
  BarChart3,
  FlaskConical,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"

const pillars: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: ShieldCheck,
    title: "Security evidence",
    description:
      "Static-analysis evidence grounds security reasoning in the actual changed code.",
  },
  {
    icon: FlaskConical,
    title: "Generated tests",
    description:
      "Tests are generated for modified functions and executed in an isolated Docker sandbox.",
  },
  {
    icon: BarChart3,
    title: "Measured results",
    description:
      "Coverage before and after is measured, and a deterministic Merge Readiness score is computed.",
  },
]

const chain = [
  "Code changes",
  "Security analysis",
  "Testing assistance",
  "Actionable feedback",
]

export function SecurityTestingSection() {
  return (
    <LandingSection
      id="security-testing"
      eyebrow="Security + testing"
      title="Beyond a simple code review assistant"
    >
      <div className="grid gap-4 md:grid-cols-3">
        {pillars.map((pillar) => (
          <div key={pillar.title} className="card-lift rounded-lg border border-border bg-card p-5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 text-primary">
              <pillar.icon className="h-4 w-4" />
            </span>
            <h3 className="mt-3 font-semibold">{pillar.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {pillar.description}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        {chain.map((step, index) => (
          <Fragment key={step}>
            {index > 0 ? (
              <ArrowRight
                className="hidden h-4 w-4 text-muted-foreground sm:block"
                aria-hidden="true"
              />
            ) : null}
            <span className="rounded-full border border-border bg-card px-3 py-1 text-sm text-muted-foreground">
              {step}
            </span>
          </Fragment>
        ))}
      </div>
    </LandingSection>
  )
}