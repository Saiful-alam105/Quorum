import {
  ClipboardCheck,
  FolderGit2,
  GitBranch,
  GitPullRequestArrow,
  History,
  MessageSquare,
  ScanSearch,
  type LucideIcon,
} from "lucide-react"

import { LandingSection } from "@/components/landing/LandingSection"
import { Badge } from "@/components/ui/Badge"

type Step = {
  icon: LucideIcon
  title: string
  description: string
  roadmap?: boolean
}

const steps: Step[] = [
  {
    icon: GitBranch,
    title: "Connect GitHub",
    description:
      "Sign in with your GitHub account. Quorum only reads the repositories you authorize.",
  },
  {
    icon: FolderGit2,
    title: "Choose a repository",
    description:
      "Install the Quorum GitHub App and select the repositories Quorum may analyze.",
  },
  {
    icon: GitPullRequestArrow,
    title: "Create a Pull Request",
    description:
      "Keep using GitHub normally — open or update a Pull Request in a connected repository.",
  },
  {
    icon: ScanSearch,
    title: "Let Quorum analyze it",
    description:
      "Quorum extracts the changes, prepares context, and runs security and testing analysis.",
  },
  {
    icon: ClipboardCheck,
    title: "Review the results",
    description:
      "Open the Quorum dashboard to see status, findings, severity, affected files, and the Merge Readiness Score.",
  },
  {
    icon: MessageSquare,
    title: "Ask Quorum",
    description:
      "Ask questions about a repository, Pull Request, or analysis result.",
    roadmap: true,
  },
  {
    icon: History,
    title: "Check Review History",
    description:
      "Return later to inspect every analysis Quorum has run on your Pull Requests.",
  },
]

export function HowToUseSection() {
  return (
    <LandingSection
      id="how-to-use"
      eyebrow="How to use Quorum"
      title="From sign-in to insights in a few steps"
    >
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((step, index) => (
          <li key={step.title} className="card-lift rounded-lg border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <span className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card font-mono text-xs font-semibold text-primary">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 text-primary">
                <step.icon className="h-4 w-4" />
              </span>
            </div>
            <h3 className="mt-3 font-semibold">{step.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {step.description}
            </p>
            {step.roadmap ? (
              <Badge variant="muted" className="mt-2">
                Roadmap
              </Badge>
            ) : null}
          </li>
        ))}
      </ol>
    </LandingSection>
  )
}