import httpx

URL = "https://api.github.com/repos/symbiosis-finance/js-sdk/commits?path=src/crosschain/config/mainnet.ts&sha=main"
TARGET_COMMIT = "514a13f9465906d95617e65a65e1c148cffa614a"


def check_latest_commit(
    client: httpx.Client | None = None,
    url: str | None = None,
    commit: str | None = None,
) -> bool:
    """Checks that latest commit in mainnet.ts is the same as the one in the repo."""
    if url is None:
        url = URL
    if commit is None:
        commit = TARGET_COMMIT
    if client is None:
        client = httpx.Client()
    response = client.get(url)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Expected a list of commits")
    if not data:
        raise ValueError("No commits found")

    latest_sha = data[0]["sha"]
    return latest_sha == commit
