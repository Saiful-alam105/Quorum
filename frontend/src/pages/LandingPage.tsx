import { Link } from "react-router-dom"

import { LandingFooter } from "@/components/landing/LandingFooter"
import { LandingNav } from "@/components/landing/LandingNav"
import { LandingSection } from "@/components/landing/LandingSection"
import { QuorumMark } from "@/components/QuorumMark"
import { buttonVariants } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNav />

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-20 text-center lg:px-6 lg:py-28">
          <QuorumMark className="mx-auto h-12 w-12 rounded-xl" />
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-semibold tracking-tight lg:text-5xl">
            AI-powered Pull Request review for developers.
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground lg:text-lg">
            Quorum analyzes GitHub Pull Requests to surface security,
            code-quality, and testing issues with evidence before you merge.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/login" className={cn(buttonVariants({ size: "lg" }), "w-full sm:w-auto")}>
              Continue with GitHub
            </Link>
            <a
              href="#how-it-works"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full sm:w-auto")}
            >
              See how Quorum works
            </a>
          </div>
        </section>

        <LandingSection
          id="how-it-works"
          eyebrow="How it works"
          title="From Pull Request to findings"
        >
          <p className="max-w-3xl text-muted-foreground">
            Quorum takes a GitHub Pull Request through a structured analysis
            pipeline — from receiving the Pull Request and extracting its
            changes, to preparing bounded context, running analysis, and
            presenting findings and recommendations.
          </p>
        </LandingSection>

        <LandingSection
          id="features"
          eyebrow="Capabilities"
          title="Core capabilities"
        >
          <p className="max-w-3xl text-muted-foreground">
            Security analysis, Pull Request analysis, context management,
            analysis history, and a central review dashboard — grounded in the
            Quorum roadmap.
          </p>
        </LandingSection>

        <LandingSection
          id="architecture"
          eyebrow="Architecture"
          title="How Quorum is built"
        >
          <p className="max-w-3xl text-muted-foreground">
            GitHub webhooks and the GitHub API feed a FastAPI backend. The
            Quorum orchestrator drives the analysis pipeline, and results are
            stored in PostgreSQL for the web dashboard.
          </p>
        </LandingSection>

        <LandingSection
          id="why-quorum"
          eyebrow="Why Quorum"
          title="Built for developers"
        >
          <p className="max-w-3xl text-muted-foreground">
            A GitHub-native, evidence-driven review workflow with structured
            findings and a centralized dashboard.
          </p>
        </LandingSection>
      </main>

      <LandingFooter />
    </div>
  )
}