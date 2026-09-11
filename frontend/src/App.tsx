import { BrowserRouter, Route, Routes } from "react-router-dom"

import { AppLayout } from "@/components/AppLayout"
import AskQuorumPage from "@/pages/AskQuorumPage"
import DashboardPage from "@/pages/DashboardPage"
import LoginPage from "@/pages/LoginPage"
import NotFoundPage from "@/pages/NotFoundPage"
import PullRequestDetailPage from "@/pages/PullRequestDetailPage"
import PullRequestsPage from "@/pages/PullRequestsPage"
import RepositoriesPage from "@/pages/RepositoriesPage"
import RepositoryDetailPage from "@/pages/RepositoryDetailPage"
import ReviewsPage from "@/pages/ReviewsPage"
import SettingsPage from "@/pages/SettingsPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="repositories" element={<RepositoriesPage />} />
          <Route
            path="repositories/:repositoryId"
            element={<RepositoryDetailPage />}
          />
          <Route path="pull-requests" element={<PullRequestsPage />} />
          <Route
            path="pull-requests/:pullRequestId"
            element={<PullRequestDetailPage />}
          />
          <Route path="reviews" element={<ReviewsPage />} />
          <Route path="ask-quorum" element={<AskQuorumPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
