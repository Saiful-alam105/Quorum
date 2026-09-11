const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
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
