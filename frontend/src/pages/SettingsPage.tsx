import { Settings } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Your GitHub account, connected repositories, and preferences."
      />
      <EmptyState
        icon={Settings}
        title="Settings are not available yet"
        description="Account information, GitHub App authorization status, and preferences will appear here once the authentication and repository APIs are exposed to the dashboard."
      />
    </>
  )
}
