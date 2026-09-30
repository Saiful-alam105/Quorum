import base64
from urllib.parse import quote

import httpx

from quorum.github.app_auth import github_client, retry_github

GITHUB_API_BASE = "https://api.github.com"


async def _request(
    method: str,
    url: str,
    *,
    token: str,
    params: dict | None = None,
    json: dict | None = None,
    accept: str = "application/vnd.github+json",
) -> httpx.Response:
    """Perform a GitHub API request with a generous timeout and retries.

    Pipeline-critical GitHub calls are the most failure-prone step on flaky or
    slow connections (quick tunnel overhead included), so transient network
    errors are retried with backoff instead of failing the whole analysis.
    """

    async def attempt() -> httpx.Response:
        async with github_client() as client:
            call = getattr(client, method)
            kwargs: dict = {
                "headers": {
                    "Authorization": f"Bearer {token}",
                    "Accept": accept,
                },
                "params": params,
            }
            if json is not None:
                kwargs["json"] = json
            response = await call(url, **kwargs)
            response.raise_for_status()
            return response

    return await retry_github(attempt)


async def get_repositories(token: str) -> list[dict]:
    response = await _request(
        "get", f"{GITHUB_API_BASE}/user/repos", token=token, params={"per_page": 100}
    )
    return response.json()


async def get_authenticated_user(token: str) -> dict:
    response = await _request("get", f"{GITHUB_API_BASE}/user", token=token)
    return response.json()


async def get_repository(token: str, owner: str, repo: str) -> dict:
    response = await _request(
        "get", f"{GITHUB_API_BASE}/repos/{owner}/{repo}", token=token
    )
    return response.json()


async def get_pull_request(token: str, owner: str, repo: str, pr_number: int) -> dict:
    response = await _request(
        "get", f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}", token=token
    )
    return response.json()


async def get_pr_files(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
        token=token,
        params={"per_page": 100},
    )
    return response.json()


async def get_pr_diff(token: str, owner: str, repo: str, pr_number: int) -> str:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
        token=token,
        accept="application/vnd.github.diff",
    )
    return response.text


async def get_file_contents(
    token: str, owner: str, repo: str, path: str, ref: str
) -> str:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{quote(path, safe='/')}",
        token=token,
        params={"ref": ref},
    )
    data = response.json()
    content = data.get("content", "")
    return base64.b64decode(content).decode("utf-8")


async def get_pr_comments(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/comments",
        token=token,
    )
    return response.json()


async def list_branches(token: str, owner: str, repo: str) -> list[str]:
    """List branch names for a repository."""
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches",
        token=token,
        params={"per_page": 100},
    )
    return [branch.get("name", "") for branch in response.json()]


async def create_pull_request(
    token: str,
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str | None = None,
) -> dict:
    """Create a pull request on GitHub and return the created PR object."""
    payload: dict = {"title": title, "head": head, "base": base}
    if body:
        payload["body"] = body
    response = await _request(
        "post", f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls", token=token, json=payload
    )
    return response.json()


async def get_user_installations(token: str) -> list[dict]:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/user/installations",
        token=token,
        params={"per_page": 100},
    )
    return response.json().get("installations", [])


async def get_installation_repositories(token: str) -> list[dict]:
    response = await _request(
        "get",
        f"{GITHUB_API_BASE}/installation/repositories",
        token=token,
        params={"per_page": 100},
    )
    return response.json().get("repositories", [])


async def create_pr_comment(
    token: str, owner: str, repo: str, pr_number: int, body: str
) -> dict:
    response = await _request(
        "post",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
        token=token,
        json={"body": body},
    )
    return response.json()


async def merge_pull_request(
    token: str,
    owner: str,
    repo: str,
    pr_number: int,
    commit_title: str,
    commit_message: str | None = None,
    merge_method: str = "merge",
) -> dict:
    """Merge a pull request on GitHub and return the merge result."""
    payload: dict = {"merge_method": merge_method}
    if commit_title:
        payload["commit_title"] = commit_title
    if commit_message:
        payload["commit_message"] = commit_message
    response = await _request(
        "put",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/merge",
        token=token,
        json=payload,
    )
    return response.json()


async def close_pull_request(
    token: str, owner: str, repo: str, pr_number: int
) -> dict:
    """Close a pull request on GitHub (without merging)."""
    response = await _request(
        "patch",
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
        token=token,
        json={"state": "closed"},
    )
    return response.json()