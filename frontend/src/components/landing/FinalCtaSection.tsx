import { Link } from "react-router-dom"

import { buttonVariants } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

export function FinalCtaSection() {
  return (
    <section className="relative overflow-hidden border-t border-border/60">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 mx-auto h-64 max-w-4xl bg-primary/10 blur-3xl"
      />
      <div className="relative mx-auto max-w-4xl px-4 py-20 text-center lg:px-6 lg:py-24">
        <h2 className="text-3xl font-semibold tracking-tight lg:text-4xl">
          Bring Quorum into your Pull Request workflow.
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
          Sign in with GitHub and connect the repositories you review.
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
            Explore the workflow
          </a>
        </div>
      </div>
    </section>
  )
}