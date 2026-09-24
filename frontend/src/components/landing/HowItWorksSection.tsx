import { LandingSection } from "@/components/landing/LandingSection"

const steps = [
  {
    title: "Quorum receives the Pull Request",
    description:
      "GitHub sends the Pull Request event through a signature-verified webhook.",
  },
  {
    title: "Changed code is extracted",
    description:
      "Quorum parses the diff and the Python structure of the changed files.",
  },
  {
    title: "Context is prepared",
    description:
      "Relevant code context is selected and bounded to what the analysis needs.",
  },
  {
    title: "The analysis pipeline runs",
    description:
      "Security evidence, generated tests, and coverage are produced and measured.",
  },
  {
    title: "Merge Readiness is scored",
    description:
      "A deterministic 0–100 score is computed from the measured evidence.",
  },
  {
    title: "Findings are presented",
    description:
      "Results appear in the dashboard and as a review summary on the Pull Request.",
  },
]

export function HowItWorksSection() {
  return (
    <LandingSection
      id="how-it-works"
      eyebrow="How it works"
      title="From Pull Request to findings"
    >
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((step, index) => (
          <li key={step.title} className="rounded-lg border border-border bg-card p-5">
            <span className="font-mono text-sm font-semibold text-primary">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-2 font-semibold">{step.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {step.description}
            </p>
          </li>
        ))}
      </ol>
    </LandingSection>
  )
}