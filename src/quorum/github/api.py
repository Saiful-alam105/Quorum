import base64
from urllib.parse import quote

import httpx

GITHUB_API_BASE = "https://api.github.com"


async def get_repositories(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": 100},
        )
        response.raise_for_status()
        return response.json()


async def get_authenticated_user(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_repository(token: str, owner: str, repo: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_pull_request(token: str, owner: str, repo: str, pr_number: int) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_pr_files(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_pr_diff(token: str, owner: str, repo: str, pr_number: int) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.diff",
            },
        )
        response.raise_for_status()
        return response.text


async def get_file_contents(
    token: str, owner: str, repo: str, path: str, ref: str
) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{quote(path, safe='/')}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"ref": ref},
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8")


async def get_pr_comments(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def list_branches(token: str, owner: str, repo: str) -> list[str]:
    """List branch names for a repository."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": 100},
        )
        response.raise_for_status()
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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def get_user_installations(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user/installations",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": 100},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("installations", [])


async def get_installation_repositories(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/installation/repositories",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": 100},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("repositories", [])


async def create_pr_comment(
    token: str, owner: str, repo: str, pr_number: int, body: str
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"body": body},
        )
        response.raise_for_status()
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
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def close_pull_request(
    token: str, owner: str, repo: str, pr_number: int
) -> dict:
    """Close a pull request on GitHub (without merging)."""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"state": "closed"},
        )
        response.raise_for_status()
        return response.json()
