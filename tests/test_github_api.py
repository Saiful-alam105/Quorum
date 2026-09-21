import base64

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from quorum.github.api import (
    create_pr_comment,
    get_authenticated_user,
    get_file_contents,
    get_installation_repositories,
    get_pr_comments,
    get_pr_diff,
    get_pr_files,
    get_pull_request,
    get_repositories,
    get_repository,
    get_user_installations,
)


@pytest.fixture
def mock_token():
    return "test_token_123"


@pytest.fixture
def mock_owner():
    return "test-owner"


@pytest.fixture
def mock_repo():
    return "test-repo"


@pytest.fixture
def mock_pr_number():
    return 42


def _make_mock_response(json_data=None, text_data=None):
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.text = text_data
    mock_response.raise_for_status = MagicMock()
    return mock_response


class TestGetRepositories:
    @pytest.mark.asyncio
    async def test_get_repositories_success(self, mock_token):
        mock_response = [
            {"id": 1, "name": "repo1", "full_name": "user/repo1"},
            {"id": 2, "name": "repo2", "full_name": "user/repo2"},
        ]

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_repositories(mock_token)

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/user/repos" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_token}"

    @pytest.mark.asyncio
    async def test_get_repositories_empty(self, mock_token):
        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=[])

            result = await get_repositories(mock_token)

            assert result == []


class TestGetAuthenticatedUser:
    @pytest.mark.asyncio
    async def test_get_authenticated_user_success(self, mock_token):
        mock_response = {
            "id": 12345,
            "login": "octocat",
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_authenticated_user(mock_token)

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/user" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_token}"


class TestGetRepository:
    @pytest.mark.asyncio
    async def test_get_repository_success(self, mock_token, mock_owner, mock_repo):
        mock_response = {
            "id": 123,
            "name": mock_repo,
            "full_name": f"{mock_owner}/{mock_repo}",
            "private": False,
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_repository(mock_token, mock_owner, mock_repo)

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert f"/repos/{mock_owner}/{mock_repo}" in call_args[0][0]


class TestGetPullRequest:
    @pytest.mark.asyncio
    async def test_get_pull_request_success(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        mock_response = {
            "id": 1,
            "number": mock_pr_number,
            "title": "Test PR",
            "state": "open",
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_pull_request(
                mock_token, mock_owner, mock_repo, mock_pr_number
            )

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert f"/repos/{mock_owner}/{mock_repo}/pulls/{mock_pr_number}" in call_args[0][0]


class TestGetPrFiles:
    @pytest.mark.asyncio
    async def test_get_pr_files_success(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        mock_response = [
            {
                "filename": "file1.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
            },
            {"filename": "file2.py", "status": "added", "additions": 20, "deletions": 0},
        ]

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_pr_files(mock_token, mock_owner, mock_repo, mock_pr_number)

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert (
                f"/repos/{mock_owner}/{mock_repo}/pulls/{mock_pr_number}/files"
                in call_args[0][0]
            )


class TestGetPrDiff:
    @pytest.mark.asyncio
    async def test_get_pr_diff_success(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        mock_diff = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3"""

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(text_data=mock_diff)

            result = await get_pr_diff(mock_token, mock_owner, mock_repo, mock_pr_number)

            assert result == mock_diff
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[1]["headers"]["Accept"] == "application/vnd.github.diff"


class TestGetFileContents:
    @pytest.mark.asyncio
    async def test_get_file_contents_decodes_base64(
        self, mock_token, mock_owner, mock_repo
    ):
        content = "def hello():\n    return 1\n"
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        mock_response = {"content": encoded, "encoding": "base64"}

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_file_contents(
                mock_token, mock_owner, mock_repo, "src/app.py", "abc123"
            )

            assert result == content
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert (
                f"/repos/{mock_owner}/{mock_repo}/contents/src/app.py"
                in call_args[0][0]
            )
            assert call_args[1]["params"] == {"ref": "abc123"}
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_token}"

    @pytest.mark.asyncio
    async def test_get_file_contents_empty_content(
        self, mock_token, mock_owner, mock_repo
    ):
        mock_response = {"content": "", "encoding": "base64"}

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_file_contents(
                mock_token, mock_owner, mock_repo, "empty.txt", "abc123"
            )
            assert result == ""


class TestGetUserInstallations:
    @pytest.mark.asyncio
    async def test_get_user_installations_success(self, mock_token):
        mock_response = {
            "total_count": 1,
            "installations": [{"id": 555, "account": {"login": "octocat"}}],
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_user_installations(mock_token)

            assert result == [{"id": 555, "account": {"login": "octocat"}}]
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/user/installations" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_token}"


class TestGetInstallationRepositories:
    @pytest.mark.asyncio
    async def test_get_installation_repositories_success(self, mock_token):
        mock_response = {
            "total_count": 1,
            "repositories": [
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "private": False,
                    "owner": {"login": "user"},
                }
            ],
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_installation_repositories(mock_token)

            assert result == [
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "private": False,
                    "owner": {"login": "user"},
                }
            ]
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/installation/repositories" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_token}"


class TestGetPrComments:
    @pytest.mark.asyncio
    async def test_get_pr_comments_success(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        mock_response = [
            {
                "id": 1,
                "body": "First comment",
                "user": {"login": "user1"},
            },
            {
                "id": 2,
                "body": "Second comment",
                "user": {"login": "user2"},
            },
        ]

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = _make_mock_response(json_data=mock_response)

            result = await get_pr_comments(
                mock_token, mock_owner, mock_repo, mock_pr_number
            )

            assert result == mock_response
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert (
                f"/repos/{mock_owner}/{mock_repo}/pulls/{mock_pr_number}/comments"
                in call_args[0][0]
            )


class TestCreatePrComment:
    @pytest.mark.asyncio
    async def test_create_pr_comment_success(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        comment_body = "This is a test comment from Quorum"
        mock_response = {
            "id": 123,
            "body": comment_body,
            "user": {"login": "quorum-bot"},
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_mock_response(json_data=mock_response)

            result = await create_pr_comment(
                mock_token, mock_owner, mock_repo, mock_pr_number, comment_body
            )

            assert result == mock_response
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert (
                f"/repos/{mock_owner}/{mock_repo}/issues/{mock_pr_number}/comments"
                in call_args[0][0]
            )
            assert call_args[1]["json"]["body"] == comment_body

    @pytest.mark.asyncio
    async def test_create_pr_comment_with_markdown(
        self, mock_token, mock_owner, mock_repo, mock_pr_number
    ):
        comment_body = """## Quorum Review

**Score:** 85/100

### Security Issues
- No critical issues found

### Test Coverage
- Coverage: 92%"""

        mock_response = {
            "id": 124,
            "body": comment_body,
        }

        with patch("quorum.github.api.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = _make_mock_response(json_data=mock_response)

            result = await create_pr_comment(
                mock_token, mock_owner, mock_repo, mock_pr_number, comment_body
            )

            assert result == mock_response
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["body"] == comment_body
