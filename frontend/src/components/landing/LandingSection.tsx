import type { ReactNode } from "react"

export function LandingSection({
  id,
  eyebrow,
  title,
  children,
}: {
  id?: string
  eyebrow?: string
  title: string
  children?: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-16 border-t border-border/60">
      <div className="mx-auto max-w-6xl px-4 py-16 lg:px-6 lg:py-20">
        {eyebrow ? (
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="text-2xl font-semibold tracking-tight lg:text-3xl">
          {title}
        </h2>
        {children ? <div className="mt-6">{children}</div> : null}
      </div>
    </section>
  )
}