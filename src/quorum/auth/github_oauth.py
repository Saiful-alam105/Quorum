import httpx

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def build_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = (
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    return GITHUB_AUTHORIZE_URL + params


async def exchange_code(client_id: str, client_secret: str, code: str) -> str:
    async with httpx.AsyncClient() as http:
        response = await http.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            },
        )
        response.raise_for_status()
        data = response.json()

    access_token = data.get("access_token", "")
    if not access_token:
        error = data.get("error_description", data.get("error", "unknown error"))
        raise ValueError(f"GitHub OAuth error: {error}")
    return access_token


async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as http:
        response = await http.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()
