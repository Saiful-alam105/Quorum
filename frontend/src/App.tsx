import { BrowserRouter, Route, Routes } from "react-router-dom"

import { AppLayout } from "@/components/AppLayout"
import AskQuorumPage from "@/pages/AskQuorumPage"
import FindingsPage from "@/pages/FindingsPage"
import HomePage from "@/pages/HomePage"
import LoginPage from "@/pages/LoginPage"
import NotFoundPage from "@/pages/NotFoundPage"
import ProfilePage from "@/pages/ProfilePage"
import PullRequestDetailPage from "@/pages/PullRequestDetailPage"
import PullRequestsPage from "@/pages/PullRequestsPage"
import RepositoriesPage from "@/pages/RepositoriesPage"
import RepositoryDetailPage from "@/pages/RepositoryDetailPage"
import ReviewDetailPage from "@/pages/ReviewDetailPage"
import ReviewsPage from "@/pages/ReviewsPage"
import SettingsPage from "@/pages/SettingsPage"

export default function App() {
  return (
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<HomePage />} />
        <Route element={<AppLayout />}>
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
          <Route path="reviews/:reviewId" element={<ReviewDetailPage />} />
          <Route path="findings" element={<FindingsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="ask-quorum" element={<AskQuorumPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}