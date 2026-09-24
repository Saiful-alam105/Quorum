import { Link } from "react-router-dom"
import { GitPullRequestArrow } from "lucide-react"

import { ArchitectureSection } from "@/components/landing/ArchitectureSection"
import { CapabilitiesSection } from "@/components/landing/CapabilitiesSection"
import { FinalCtaSection } from "@/components/landing/FinalCtaSection"
import { HowItWorksSection } from "@/components/landing/HowItWorksSection"
import { LandingFooter } from "@/components/landing/LandingFooter"
import { LandingNav } from "@/components/landing/LandingNav"
import { ProblemSection } from "@/components/landing/ProblemSection"
import { ReviewExperienceSection } from "@/components/landing/ReviewExperienceSection"
import { SecurityTestingSection } from "@/components/landing/SecurityTestingSection"
import { WhyQuorumSection } from "@/components/landing/WhyQuorumSection"
import { SeverityDot } from "@/components/severity"
import { buttonVariants } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

function HeroPreview() {
  return (
    <div className="mx-auto mt-16 max-w-2xl">
      <div className="rounded-xl border border-border bg-card/80 p-6 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/40 bg-primary/15 text-primary">
              <GitPullRequestArrow className="h-4 w-4" />
            </span>
            <div>
              <p className="font-medium">Pull Request #42</p>
              <p className="text-xs text-muted-foreground">
                Add authentication to the API
              </p>
            </div>
          </div>
          <span className="rounded-full border border-success/40 bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
            Analysis completed
          </span>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Security</p>
            <ul className="mt-2 space-y-1.5 text-sm">
              <li className="flex items-center gap-2">
                <SeverityDot severity="high" />
                <span className="text-muted-foreground">2 high</span>
              </li>
              <li className="flex items-center gap-2">
                <SeverityDot severity="medium" />
                <span className="text-muted-foreground">1 medium</span>
              </li>
            </ul>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Tests</p>
            <p className="mt-2 text-sm text-muted-foreground">
              4 generated · 4 passed
            </p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Merge Readiness</p>
            <p className="mt-2 font-mono text-2xl font-semibold">
              82
              <span className="text-xs text-muted-foreground">/100</span>
            </p>
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        Product preview — example review outcome
      </p>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNav />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border/60">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 top-0 mx-auto h-72 max-w-4xl bg-primary/10 blur-3xl"
          />
          <div className="relative mx-auto max-w-6xl px-4 py-20 text-center lg:px-6 lg:py-28">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              AI-powered Pull Request review
            </span>
            <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-semibold tracking-tight lg:text-5xl">
              Understand every Pull Request before you merge.
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground lg:text-lg">
              Quorum analyzes GitHub Pull Requests with security, code-quality,
              and testing analysis — producing actionable findings and a
              deterministic Merge Readiness Score.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                to="/login"
                className={cn(buttonVariants({ size: "lg" }), "w-full sm:w-auto")}
              >
                Continue with GitHub
              </Link>
              <a
                href="#how-it-works"
                className={cn(
                  buttonVariants({ variant: "outline", size: "lg" }),
                  "w-full sm:w-auto",
                )}
              >
                See how Quorum works
              </a>
            </div>
          </div>
          <div className="relative px-4 pb-20 lg:px-6">
            <HeroPreview />
          </div>
        </section>

        <ProblemSection />

        <HowItWorksSection />

        <CapabilitiesSection />

        <ReviewExperienceSection />

        <SecurityTestingSection />

        <ArchitectureSection />

        <WhyQuorumSection />
      </main>

      <FinalCtaSection />

      <LandingFooter />
    </div>
  )
}