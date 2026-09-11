import { FolderGit2 } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function RepositoriesPage() {
  return (
    <>
      <PageHeader
        title="Repositories"
        description="Repositories connected through the Quorum GitHub App."
      />
      <EmptyState
        icon={FolderGit2}
        title="No repositories to show yet"
        description="This view will list the repositories Quorum can access. The backend read API for repositories is not available yet, so there is nothing to display."
      />
    </>
  )
}
