const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    ...init,
  })

  if (!response.ok) {
    throw new ApiError(response.status, `Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

export type HealthResponse = {
  status: string
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health")
}

export type Repository = {
  id: number
  github_id: number
  owner: string
  name: string
  full_name: string
  is_private: boolean
  pull_request_count: number
  open_pull_request_count: number
  latest_analysis_status: string | null
}

export function getRepositories(): Promise<Repository[]> {
  return request<Repository[]>("/api/repositories")
}

export function getRepository(id: number): Promise<Repository> {
  return request<Repository>(`/api/repositories/${id}`)
}

export function getRepositoryPullRequests(
  id: number,
): Promise<PullRequestSummary[]> {
  return request<PullRequestSummary[]>(`/api/repositories/${id}/pull-requests`)
}

export type PullRequestSummary = {
  id: number
  github_id: number
  number: number
  title: string
  author: string
  state: string
  repository_id: number | null
  repository_full_name: string | null
  updated_at: string | null
  latest_analysis_status: string | null
  merge_readiness_score: number | null
  finding_count: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  test_count: number
}

export function getPullRequests(): Promise<PullRequestSummary[]> {
  return request<PullRequestSummary[]>("/api/pull-requests")
}

export function getPullRequest(id: number): Promise<PullRequestSummary> {
  return request<PullRequestSummary>(`/api/pull-requests/${id}`)
}

export type AnalysisRun = {
  id: number
  pull_request_id: number
  status: string
  merge_readiness_score: number | null
  started_at: string | null
  completed_at: string | null
  recommendation: string | null
}

export function getPullRequestAnalysis(id: number): Promise<AnalysisRun[]> {
  return request<AnalysisRun[]>(`/api/pull-requests/${id}/analysis`)
}

export function getPullRequestSecurity(
  id: number,
): Promise<SecurityFinding[]> {
  return request<SecurityFinding[]>(`/api/pull-requests/${id}/security`)
}

export function getPullRequestTests(id: number): Promise<TestRun[]> {
  return request<TestRun[]>(`/api/pull-requests/${id}/tests`)
}

export function getPullRequestCoverage(
  id: number,
): Promise<CoverageResult | null> {
  return request<CoverageResult | null>(`/api/pull-requests/${id}/coverage`)
}

export type Finding = {
  id: number
  analysis_run_id: number
  rule_id: string | null
  severity: string
  title: string
  file: string
  line: number | null
  evidence: string
  explanation: string | null
  confidence: number | null
  pull_request_id: number
  pr_number: number
  pr_title: string
  repository_id: number
  repository_full_name: string
}

export function getFindings(limit = 10): Promise<Finding[]> {
  return request<Finding[]>(`/api/findings?limit=${limit}`)
}

export type ReviewSummary = {
  id: number
  pull_request_id: number
  pr_number: number
  pr_title: string
  pr_author: string
  pr_state: string
  repository_id: number
  repository_full_name: string
  status: string
  merge_readiness_score: number | null
  recommendation: string | null
  started_at: string | null
  completed_at: string | null
  finding_count: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  test_count: number
  coverage_before: number | null
  coverage_after: number | null
  coverage_delta: number | null
}

export function getReviews(): Promise<ReviewSummary[]> {
  return request<ReviewSummary[]>("/api/reviews")
}

export type ReviewDetail = ReviewSummary & {
  findings: SecurityFinding[]
  tests: TestRun[]
  coverage: CoverageResult | null
}

export function getReview(id: number): Promise<ReviewDetail> {
  return request<ReviewDetail>(`/api/reviews/${id}`)
}

export type ChatMessage = {
  id: number
  analysis_run_id: number
  role: "user" | "assistant"
  message: string
  timestamp: string
}

export function getChatMessages(reviewId: number): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/api/reviews/${reviewId}/chat`)
}

export function postChatMessage(
  reviewId: number,
  question: string,
): Promise<{ answer: string }> {
  return request<{ answer: string }>(`/api/reviews/${reviewId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  })
}

export type SecurityFinding = {
  id: number
  analysis_run_id: number
  rule_id: string | null
  severity: string
  title: string
  file: string
  line: number | null
  evidence: string
  explanation: string | null
  confidence: number | null
}

export type TestRun = {
  id: number
  analysis_run_id: number
  test_name: string
  status: string
  duration: number | null
  stdout: string | null
  stderr: string | null
  failure_reason: string | null
}

export type CoverageResult = {
  id: number
  analysis_run_id: number
  coverage_before: number | null
  coverage_after: number | null
  coverage_delta: number | null
}

export type CurrentUser = {
  github_id: number | null
  username: string | null
  avatar_url: string | null
  created_at: string | null
  github_authorized: boolean
}

export function getCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>("/auth/me")
}

export function getMe(): Promise<CurrentUser> {
  return request<CurrentUser>("/api/me")
}

export type LoginUrl = {
  authorize_url: string
}

export function getLoginUrl(): Promise<LoginUrl> {
  return request<LoginUrl>("/auth/login")
}

export function logout(): Promise<{ status: string }> {
  return request<{ status: string }>("/auth/logout", { method: "POST" })
}
