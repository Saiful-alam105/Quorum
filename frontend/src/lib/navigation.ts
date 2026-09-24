import {
  ClipboardCheck,
  FolderGit2,
  GitPullRequest,
  LayoutDashboard,
  MessageSquare,
  Settings,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react"

export type NavItem = {
  label: string
  to: string
  icon: LucideIcon
}

export const navItems: NavItem[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Repositories", to: "/repositories", icon: FolderGit2 },
  { label: "Pull Requests", to: "/pull-requests", icon: GitPullRequest },
  { label: "Reviews", to: "/reviews", icon: ClipboardCheck },
  { label: "Findings", to: "/findings", icon: ShieldAlert },
  { label: "Ask Quorum", to: "/ask-quorum", icon: MessageSquare },
  { label: "Settings", to: "/settings", icon: Settings },
]
