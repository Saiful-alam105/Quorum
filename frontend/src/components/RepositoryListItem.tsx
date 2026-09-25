import { Link } from "react-router-dom"
import { ExternalLink, FolderGit2, Lock } from "lucide-react"

import { AnalysisStatusBadge } from "@/components/status"
import type { Repository } from "@/lib/api"

export function RepositoryListItem({ repository }: { repository: Repository }) {
  const prCount = repository.pull_request_count

  return (
    <li className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-card p-4">
      <Link
        to={`/repositories/${repository.id}`}
        className="min-w-0 space-y-1.5"
      >
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate font-medium transition-colors hover:text-primary hover:underline">
            {repository.full_name}
          </span>
          {repository.is_private ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              Private
            </span>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">
          {prCount} {prCount === 1 ? "pull request" : "pull requests"} ·{" "}
          {repository.open_pull_request_count} open
        </p>
      </Link>
      <div className="flex shrink-0 items-center gap-3">
        <AnalysisStatusBadge status={repository.latest_analysis_status} />
        <a
          href={`https://github.com/${repository.full_name}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          GitHub
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </li>
  )
}