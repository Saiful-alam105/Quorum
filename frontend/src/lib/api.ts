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
}

export function getRepositories(): Promise<Repository[]> {
  return request<Repository[]>("/api/repositories")
}

export function getRepository(id: number): Promise<Repository> {
  return request<Repository>(`/api/repositories/${id}`)
}

export type PullRequest = {
  id: number
  github_id: number
  number: number
  title: string
  author: string
  state: string
}

export function getRepositoryPullRequests(id: number): Promise<PullRequest[]> {
  return request<PullRequest[]>(`/api/repositories/${id}/pull-requests`)
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
}

export function getPullRequests(): Promise<PullRequestSummary[]> {
  return request<PullRequestSummary[]>("/api/pull-requests")
}

export function getPullRequest(id: number): Promise<PullRequestSummary> {
  return request<PullRequestSummary>(`/api/pull-requests/${id}`)
}

export type CurrentUser = {
  github_id: number | null
  username: string | null
  avatar_url: string | null
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
