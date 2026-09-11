from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    github_id: int | None
    username: str | None


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
