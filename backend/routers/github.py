import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.github import build_repo_document, fetch_pinned_repos, fetch_repo_readme
from utils.rag import github_rag

router = APIRouter(prefix="/github", tags=["github"])


class IndexRequest(BaseModel):
    username: str


@router.post("/index")
def index_github_repos(request: IndexRequest):
    """Fetch the user's pinned GitHub repos and index them in ChromaDB."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")

    repos = fetch_pinned_repos(request.username, token)
    if not repos:
        raise HTTPException(status_code=404, detail="No pinned repos found for this user")

    documents = []
    repo_names = []
    for repo in repos:
        readme = fetch_repo_readme(request.username, repo["name"], token)
        doc = build_repo_document(repo, readme)
        documents.append(doc)
        repo_names.append(repo["name"])

    github_rag.index_repos(documents, repo_names)

    return {
        "indexed": len(documents),
        "repos": repo_names,
    }


@router.get("/repos")
def list_indexed_repos():
    """Return the list of GitHub repos currently indexed in ChromaDB."""
    return {"repos": github_rag.list_repos()}
