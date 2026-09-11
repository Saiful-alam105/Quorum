import { Loader2 } from "lucide-react"

type LoadingStateProps = {
  label?: string
}

export function LoadingState({ label = "Loading…" }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-lg border border-dashed border-border p-12 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{label}</span>
    </div>
  )
}
