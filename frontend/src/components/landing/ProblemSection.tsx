import { LandingSection } from "@/components/landing/LandingSection"

const problems = [
  {
    title: "Security issues slip through",
    description:
      "Vulnerable patterns in changed code can be easy to miss during a busy review.",
  },
  {
    title: "Coverage gaps hide regressions",
    description:
      "Without testing feedback, risky changes can land with untested paths.",
  },
  {
    title: "Reviews get repetitive",
    description:
      "Re-identifying the same kinds of issues over and over slows a whole team down.",
  },
]

export function ProblemSection() {
  return (
    <LandingSection
      id="problem"
      eyebrow="The problem"
      title="Pull Requests deserve more than a quick look."
    >
      <div className="grid gap-4 md:grid-cols-3">
        {problems.map((problem) => (
          <div key={problem.title} className="rounded-lg border border-border bg-card p-5">
            <h3 className="font-semibold">{problem.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {problem.description}
            </p>
          </div>
        ))}
      </div>
    </LandingSection>
  )
}