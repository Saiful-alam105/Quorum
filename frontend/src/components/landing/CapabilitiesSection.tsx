import {
  BarChart3,
  Code2,
  FlaskConical,
  History,
  MessageSquare,
  ScanSearch,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"
import { Badge } from "@/components/ui/Badge"

type Capability = {
  icon: LucideIcon
  title: string
  description: string
  roadmap?: boolean
}

const capabilities: Capability[] = [
  {
    icon: ShieldCheck,
    title: "Security analysis",
    description:
      "Static-analysis evidence combined with AI reasoning over the changed code.",
  },
  {
    icon: Code2,
    title: "Pull Request analysis",
    description:
      "The diff and Python structure of changed files are extracted and analyzed.",
  },
  {
    icon: ScanSearch,
    title: "Context management",
    description:
      "Relevant context is selected and bounded so analysis stays focused.",
  },
  {
    icon: FlaskConical,
    title: "Testing assistance",
    description:
      "Tests are generated and executed in an isolated sandbox, with coverage measured.",
  },
  {
    icon: BarChart3,
    title: "Merge Readiness",
    description:
      "A deterministic 0–100 score is computed from the measured evidence.",
  },
  {
    icon: History,
    title: "Analysis history",
    description:
      "Previous results are stored and inspectable from the dashboard.",
  },
  {
    icon: MessageSquare,
    title: "Ask Quorum",
    description:
      "Ask questions about a repository, Pull Request, or analysis result.",
    roadmap: true,
  },
]

export function CapabilitiesSection() {
  return (
    <LandingSection
      id="features"
      eyebrow="Capabilities"
      title="Everything a Pull Request review needs"
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {capabilities.map((capability) => (
          <div key={capability.title} className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 text-primary">
                <capability.icon className="h-4 w-4" />
              </span>
              {capability.roadmap ? (
                <Badge variant="muted">Roadmap</Badge>
              ) : null}
            </div>
            <h3 className="mt-3 font-semibold">{capability.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {capability.description}
            </p>
          </div>
        ))}
      </div>
    </LandingSection>
  )
}