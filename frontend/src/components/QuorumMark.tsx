import { GitPullRequestArrow } from "lucide-react"

import { cn } from "@/lib/utils"

export function QuorumMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/15 text-primary",
        className,
      )}
    >
      <GitPullRequestArrow className="h-4 w-4" />
    </span>
  )
}