import { LandingSection } from "@/components/landing/LandingSection"

const nodes = [
  {
    title: "GitHub",
    description: "Pull Requests and repository data.",
  },
  {
    title: "Webhook / GitHub API",
    description: "Events and changed code are fetched securely.",
  },
  {
    title: "FastAPI backend",
    description: "Webhook server and REST API.",
  },
  {
    title: "Orchestrator",
    description: "Drives the analysis pipeline stages.",
  },
  {
    title: "Diff + context",
    description: "Changed code is extracted and bounded.",
  },
  {
    title: "Analysis pipeline",
    description: "Security, tests, and coverage run.",
  },
  {
    title: "PostgreSQL",
    description: "Results are stored persistently.",
  },
  {
    title: "Quorum dashboard",
    description: "Findings and scores are presented.",
  },
]

export function ArchitectureSection() {
  return (
    <LandingSection
      id="architecture"
      eyebrow="Architecture"
      title="How Quorum is built"
    >
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {nodes.map((node, index) => (
          <li key={node.title} className="rounded-lg border border-border bg-card p-5">
            <span className="font-mono text-sm font-semibold text-primary">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-2 font-semibold">{node.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {node.description}
            </p>
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