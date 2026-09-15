import httpx
import pytest
from unittest.mock import AsyncMock, patch

from quorum.config import settings
from quorum.github.diff_service import DiffFetchError, fetch_pr_diff

DIFF_TEXT = "diff --git a/app.py b/app.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"


def _http_error(status_code: int = 404) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.github.com/repos/o/r/pulls/1")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


class TestFetchPrDiff:
    @pytest.mark.asyncio
    async def test_returns_diff_text(self) -> None:
        install_mock = AsyncMock(return_value={"token": "install-token"})
        diff_mock = AsyncMock(return_value=DIFF_TEXT)
        with patch("quorum.github.diff_service.get_installation_token", install_mock), patch(
            "quorum.github.diff_service.get_pr_diff", diff_mock
        ):
            result = await fetch_pr_diff(555, "octocat", "hello-world", 7)

        assert result == DIFF_TEXT
        install_mock.assert_awaited_once_with(
            settings.github_app_id, settings.github_app_private_key_path, 555
        )
        diff_mock.assert_awaited_once_with("install-token", "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_returns_empty_diff_text(self) -> None:
        with patch(
            "quorum.github.diff_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.diff_service.get_pr_diff", AsyncMock(return_value="")
        ):
            result = await fetch_pr_diff(555, "octocat", "hello-world", 7)

        assert result == ""

    @pytest.mark.asyncio
    async def test_missing_configuration_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "github_app_id", "")
        monkeypatch.setattr(settings, "github_app_private_key_path", "")

        with pytest.raises(DiffFetchError):
            await fetch_pr_diff(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_missing_installation_id_raises(self) -> None:
        with pytest.raises(DiffFetchError):
            await fetch_pr_diff(None, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_token_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.diff_service.get_installation_token",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(DiffFetchError):
                await fetch_pr_diff(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_token_absent_from_response_raises(self) -> None:
        with patch(
            "quorum.github.diff_service.get_installation_token", AsyncMock(return_value={})
        ):
            with pytest.raises(DiffFetchError):
                await fetch_pr_diff(555, "octocat", "hello-world", 7)

    @pytest.mark.asyncio
    async def test_diff_retrieval_failure_raises(self) -> None:
        with patch(
            "quorum.github.diff_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.diff_service.get_pr_diff",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(DiffFetchError):
                await fetch_pr_diff(555, "octocat", "hello-world", 7)