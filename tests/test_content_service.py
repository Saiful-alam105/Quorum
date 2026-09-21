import httpx
import pytest
from unittest.mock import AsyncMock, patch

from quorum.config import settings
from quorum.github.content_service import (
    ContentFetchError,
    fetch_file_content,
    fetch_pull_request,
)


def _http_error(status_code: int = 404) -> httpx.HTTPStatusError:
    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/o/r/contents/src/app.py",
    )
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


class TestFetchFileContent:
    @pytest.mark.asyncio
    async def test_returns_decoded_content(self) -> None:
        install_mock = AsyncMock(return_value={"token": "install-token"})
        contents_mock = AsyncMock(return_value="def hello():\n    pass\n")
        with patch(
            "quorum.github.content_service.get_installation_token", install_mock
        ), patch(
            "quorum.github.content_service.get_file_contents", contents_mock
        ):
            result = await fetch_file_content(
                555, "octocat", "hello-world", "src/app.py", "abc123"
            )

        assert result == "def hello():\n    pass\n"
        install_mock.assert_awaited_once_with(
            settings.github_app_id, settings.github_app_private_key_path, 555
        )
        contents_mock.assert_awaited_once_with(
            "install-token", "octocat", "hello-world", "src/app.py", "abc123"
        )

    @pytest.mark.asyncio
    async def test_returns_empty_content(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.content_service.get_file_contents",
            AsyncMock(return_value=""),
        ):
            result = await fetch_file_content(
                555, "octocat", "hello-world", "empty.txt", "abc123"
            )
        assert result == ""

    @pytest.mark.asyncio
    async def test_missing_configuration_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "github_app_id", "")
        monkeypatch.setattr(settings, "github_app_private_key_path", "")

        with pytest.raises(ContentFetchError):
            await fetch_file_content(555, "octocat", "hello-world", "a.py", "ref")

    @pytest.mark.asyncio
    async def test_missing_installation_id_raises(self) -> None:
        with pytest.raises(ContentFetchError):
            await fetch_file_content(None, "octocat", "hello-world", "a.py", "ref")

    @pytest.mark.asyncio
    async def test_token_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_file_content(
                    555, "octocat", "hello-world", "a.py", "ref"
                )

    @pytest.mark.asyncio
    async def test_token_absent_from_response_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={}),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_file_content(
                    555, "octocat", "hello-world", "a.py", "ref"
                )

    @pytest.mark.asyncio
    async def test_content_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.content_service.get_file_contents",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_file_content(
                    555, "octocat", "hello-world", "a.py", "ref"
                )


class TestFetchPullRequest:
    @pytest.mark.asyncio
    async def test_returns_pull_request_dict(self) -> None:
        pr_data = {"number": 7, "head": {"sha": "abc123"}}
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.content_service.get_pull_request",
            AsyncMock(return_value=pr_data),
        ):
            result = await fetch_pull_request(555, "octocat", "hello-world", 7)

        assert result == pr_data

    @pytest.mark.asyncio
    async def test_missing_configuration_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "github_app_id", "")
        monkeypatch.setattr(settings, "github_app_private_key_path", "")

        with pytest.raises(ContentFetchError):
            await fetch_pull_request(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_missing_installation_id_raises(self) -> None:
        with pytest.raises(ContentFetchError):
            await fetch_pull_request(None, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_token_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_pull_request(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_token_absent_from_response_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={}),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_pull_request(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_pull_request_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.content_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.content_service.get_pull_request",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(ContentFetchError):
                await fetch_pull_request(555, "octocat", "hello-world", 7)