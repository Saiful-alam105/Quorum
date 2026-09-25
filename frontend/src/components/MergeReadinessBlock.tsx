import { cn } from "@/lib/utils"

export function recommendationClass(score: number): string {
  if (score >= 70) {
    return "text-success"
  }
  if (score >= 50) {
    return "text-warning"
  }
  return "text-severity-critical"
}

export function MergeReadinessBlock({
  score,
  recommendation,
  className,
}: {
  score: number | null
  recommendation: string | null
  className?: string
}) {
  if (score == null) {
    return (
      <div className={className}>
        <p className="text-sm text-muted-foreground">Merge Readiness</p>
        <p className="mt-1 text-4xl font-semibold text-muted-foreground">—</p>
        <p className="mt-1 text-sm text-muted-foreground">No score yet</p>
      </div>
    )
  }
  return (
    <div className={className}>
      <p className="text-sm text-muted-foreground">Merge Readiness</p>
      <p className="mt-1 font-mono text-4xl font-semibold">
        {score}
        <span className="text-lg text-muted-foreground">/100</span>
      </p>
      {recommendation ? (
        <p className={cn("mt-1 text-sm font-medium", recommendationClass(score))}>
          {recommendation}
        </p>
      ) : null}
    </div>
  )
}