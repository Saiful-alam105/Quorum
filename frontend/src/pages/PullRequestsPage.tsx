import { GitPullRequest } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function PullRequestsPage() {
  return (
    <>
      <PageHeader
        title="Pull Requests"
        description="Pull Requests received from GitHub webhooks."
      />
      <EmptyState
        icon={GitPullRequest}
        title="No Pull Requests to show yet"
        description="This view will list Pull Requests stored by the backend. The backend read API for Pull Requests is not available yet, so there is nothing to display."
      />
    </>
  )
}
