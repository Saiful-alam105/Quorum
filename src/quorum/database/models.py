from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quorum.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_installation_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user")
    repositories: Mapped[list["Repository"]] = relationship(back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User | None] = relationship(back_populates="repositories")
    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="repository")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    repository: Mapped[Repository] = relationship(back_populates="pull_requests")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="pull_request")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    merge_readiness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    pull_request: Mapped[PullRequest] = relationship(back_populates="analysis_runs")
    security_findings: Mapped[list["SecurityFinding"]] = relationship(
        back_populates="analysis_run"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(back_populates="analysis_run")
    coverage_results: Mapped[list["CoverageResult"]] = relationship(
        back_populates="analysis_run"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="analysis_run")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id"), index=True
    )
    rule_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    file: Mapped[str] = mapped_column(String(500))
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="security_findings")


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id"), index=True
    )
    test_name: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="generated")
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="test_runs")


class CoverageResult(Base):
    __tablename__ = "coverage_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id"), index=True
    )
    coverage_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="coverage_results")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User | None] = relationship(back_populates="chat_messages")
    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="chat_messages")