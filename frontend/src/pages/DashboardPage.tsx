import { LayoutDashboard } from "lucide-react"

import { EmptyState } from "@/components/EmptyState"
import { PageHeader } from "@/components/PageHeader"

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your Quorum review activity."
      />
      <EmptyState
        icon={LayoutDashboard}
        title="No review activity yet"
        description="The dashboard will summarize repositories, reviews, and warnings once the analysis pipeline is implemented. No data is available yet."
      />
    </>
  )
}
