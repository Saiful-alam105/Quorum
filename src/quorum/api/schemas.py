from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    github_id: int | None
    username: str | None
    avatar_url: str | None = None


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_id: int
    owner: str
    name: str
    full_name: str
    is_private: bool


class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_id: int
    number: int
    title: str
    author: str
    state: str


class PullRequestSummaryOut(BaseModel):
    id: int
    github_id: int
    number: int
    title: str
    author: str
    state: str
    repository_id: int | None
    repository_full_name: str | None
    updated_at: datetime | None = None
    latest_analysis_status: str | None = None
    merge_readiness_score: int | None = None
    finding_count: int = 0
    critical_count: int = 0
    test_count: int = 0


class FindingOut(BaseModel):
    id: int
    analysis_run_id: int
    rule_id: str | None
    severity: str
    title: str
    file: str
    line: int | None
    evidence: str
    explanation: str | None
    confidence: float | None
    pull_request_id: int
    pr_number: int
    pr_title: str
    repository_id: int
    repository_full_name: str


class AnalysisRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pull_request_id: int
    status: str
    merge_readiness_score: int | None
    started_at: datetime | None
    completed_at: datetime | None


class SecurityFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_run_id: int
    rule_id: str | None
    severity: str
    title: str
    file: str
    line: int | None
    evidence: str
    explanation: str | None
    confidence: float | None


class TestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_run_id: int
    test_name: str
    status: str
    duration: float | None
    stdout: str | None
    stderr: str | None
    failure_reason: str | None


class CoverageResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_run_id: int
    coverage_before: float | None
    coverage_after: float | None
    coverage_delta: float | None


class ReviewSummaryOut(BaseModel):
    id: int
    pull_request_id: int
    pr_number: int
    pr_title: str
    pr_author: str
    pr_state: str
    repository_id: int
    repository_full_name: str
    status: str
    merge_readiness_score: int | None
    started_at: datetime | None
    completed_at: datetime | None
    finding_count: int
    test_count: int


class ReviewDetailOut(ReviewSummaryOut):
    findings: list[SecurityFindingOut]
    tests: list[TestRunOut]
    coverage: CoverageResultOut | None
