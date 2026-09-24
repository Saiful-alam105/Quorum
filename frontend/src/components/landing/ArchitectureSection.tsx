import { LandingSection } from "@/components/landing/LandingSection"

const nodes = [
  "GitHub",
  "Webhook / GitHub API",
  "FastAPI backend",
  "Orchestrator",
  "Diff + context management",
  "Analysis pipeline",
  "PostgreSQL",
  "Quorum dashboard",
]

export function ArchitectureSection() {
  return (
    <LandingSection
      id="architecture"
      eyebrow="Architecture"
      title="How Quorum is built"
    >
      <ol className="mx-auto max-w-2xl">
        {nodes.map((node, index) => (
          <li key={node} className="flex items-stretch">
            <div className="flex flex-col items-center">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-card font-mono text-xs font-semibold text-primary">
                {index + 1}
              </span>
              {index < nodes.length - 1 ? (
                <span
                  aria-hidden="true"
                  className="my-1 w-px flex-1 bg-border"
                />
              ) : null}
            </div>
            <div className="mb-2 ml-4 rounded-lg border border-border bg-card px-4 py-2.5">
              <p className="text-sm font-medium">{node}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="mx-auto mt-6 max-w-3xl text-muted-foreground">
        GitHub events and the GitHub API feed a FastAPI backend. The Quorum
        orchestrator drives the analysis pipeline, and results are stored in
        PostgreSQL for the web dashboard and GitHub review feedback.
      </p>
    </LandingSection>
  )
}