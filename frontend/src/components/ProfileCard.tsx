import { Link } from "react-router-dom"
import { ExternalLink, Settings } from "lucide-react"

import { Avatar } from "@/components/Avatar"
import { Badge } from "@/components/ui/Badge"
import type { CurrentUser } from "@/lib/api"
import { formatDateTime } from "@/lib/format"

export function ProfileCard({ user }: { user: CurrentUser }) {
  const githubUrl = user.username
    ? `https://github.com/${user.username}`
    : null

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex flex-wrap items-center gap-4">
        <Avatar
          name={user.username}
          src={user.avatar_url}
          size="md"
          className="h-16 w-16 text-xl"
        />
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xl font-semibold">
              {user.username ?? "Quorum user"}
            </p>
            {user.github_authorized ? (
              <Badge variant="success">GitHub App authorized</Badge>
            ) : (
              <Badge variant="muted">GitHub App not installed</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            Member since{" "}
            {user.created_at ? formatDateTime(user.created_at) : "—"}
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            {githubUrl ? (
              <a
                href={githubUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {githubUrl}
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            ) : null}
            <Link
              to="/settings"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Settings className="h-3.5 w-3.5" />
              Manage
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}