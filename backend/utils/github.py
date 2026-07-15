import base64

import httpx

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"


def fetch_pinned_repos(username: str, token: str) -> list[dict]:
    query = """
        query {
        user(login: "%s") {
            pinnedItems(first: 6, types: REPOSITORY) {
            nodes {
                ... on Repository {
                name
                description
                url
                primaryLanguage { name }
                repositoryTopics(first: 10) {
                    nodes { topic { name } }
                }
                }
            }
            }
        }
        }
    """ % username

    response = httpx.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise ValueError(f"GitHub GraphQL error: {data['errors']}")
    return data["data"]["user"]["pinnedItems"]["nodes"]


def fetch_repo_readme(owner: str, repo_name: str, token: str) -> str:
    """Fetch the README content of a public GitHub repository."""
    response = httpx.get(
        f"{GITHUB_REST_URL}/repos/{owner}/{repo_name}/readme",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    if response.status_code == 404:
        return ""
    response.raise_for_status()
    # GitHub returns the README encoded in base64
    encoded_content = response.json()["content"]
    return base64.b64decode(encoded_content).decode("utf-8", errors="ignore")


def build_repo_document(repo: dict, readme: str) -> str:
    """Combine repo metadata and README into a single indexable text."""
    topics = [
        node["topic"]["name"]
        for node in repo.get("repositoryTopics", {}).get("nodes", [])
    ]
    language = (repo.get("primaryLanguage") or {}).get("name", "")

    parts = [
        f"Projet GitHub : {repo['name']}",
        f"Description : {repo.get('description') or 'Pas de description'}",
        f"URL : {repo.get('url', '')}",
    ]
    if language:
        parts.append(f"Langage principal : {language}")
    if topics:
        parts.append(f"Technologies / topics : {', '.join(topics)}")
    if readme:
        # Keep only the first 2000 characters — READMEs can be very long
        parts.append(f"README :\n{readme[:2000]}")

    return "\n".join(parts)
