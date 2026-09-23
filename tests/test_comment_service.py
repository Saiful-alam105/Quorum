import httpx
import pytest
from unittest.mock import AsyncMock, patch

from quorum.config import settings
from quorum.github.comment_service import CommentPostError, post_review_comment


def _http_error(status_code: int = 404) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://api.github.com/repos/o/r/issues/1/comments")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


class TestPostReviewComment:
    @pytest.mark.asyncio
    async def test_posts_comment(self) -> None:
        comment_data = {"id": 1, "html_url": "https://github.com/o/r/pull/1#issuecomment-1"}
        with patch(
            "quorum.github.comment_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.comment_service.create_pr_comment",
            AsyncMock(return_value=comment_data),
        ) as mock_comment:
            result = await post_review_comment(555, "octocat", "hello-world", 7, "## Quorum Review")

        assert result == comment_data
        mock_comment.assert_awaited_once_with(
            "install-token", "octocat", "hello-world", 7, "## Quorum Review"
        )

    @pytest.mark.asyncio
    async def test_missing_configuration_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "github_app_id", "")
        monkeypatch.setattr(settings, "github_app_private_key_path", "")
        with pytest.raises(CommentPostError):
            await post_review_comment(555, "octocat", "hello-world", 7, "body")

    @pytest.mark.asyncio
    async def test_missing_installation_id_raises(self) -> None:
        with pytest.raises(CommentPostError):
            await post_review_comment(None, "octocat", "hello-world", 7, "body")

    @pytest.mark.asyncio
    async def test_token_failure_raises(self) -> None:
        with patch(
            "quorum.github.comment_service.get_installation_token",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(CommentPostError):
                await post_review_comment(555, "octocat", "hello-world", 7, "body")

    @pytest.mark.asyncio
    async def test_comment_post_failure_raises(self) -> None:
        with patch(
            "quorum.github.comment_service.get_installation_token",
            AsyncMock(return_value={"token": "install-token"}),
        ), patch(
            "quorum.github.comment_service.create_pr_comment",
            AsyncMock(side_effect=_http_error()),
        ):
            with pytest.raises(CommentPostError, match="failed to post"):
                await post_review_comment(555, "octocat", "hello-world", 7, "body")