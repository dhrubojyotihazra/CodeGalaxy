"""
CodeGalaxy Backend - GitHub API Service
Fetches repository file tree and content from GitHub.
"""
import httpx
import os
import asyncio
from typing import Optional
from app.config import settings

GITHUB_API = "https://api.github.com"


def _headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CodeGalaxy-Backend/1.0"
    }
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


async def _check_git_ls_remote(owner: str, repo: str, branch: str) -> tuple[bool, str]:
    """Fallback check using git ls-remote protocol to bypass GitHub REST API rate limits."""
    github_url = f"https://github.com/{owner}/{repo}.git"
    if settings.github_token:
        github_url = f"https://{settings.github_token}@github.com/{owner}/{repo}.git"

    def _sync_ls_remote():
        import subprocess
        try:
            cmd = ["git", "ls-remote", "--heads", github_url]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout:
                output = res.stdout
                if f"refs/heads/{branch}" in output:
                    return True, branch
                if branch == "main" and "refs/heads/master" in output:
                    return True, "master"
                lines = [line for line in output.splitlines() if "refs/heads/" in line]
                if lines:
                    first_branch = lines[0].split("refs/heads/")[-1].strip()
                    return True, first_branch
            return False, branch
        except Exception:
            return False, branch

    return await asyncio.to_thread(_sync_ls_remote)


async def check_repo_exists(owner: str, repo: str, branch: str = "main") -> tuple[bool, str, Optional[str]]:
    """
    Check if the repo and branch exist.
    Returns (exists, resolved_branch, error_detail).
    """
    clean_owner = owner.strip()
    clean_repo = repo.strip().removesuffix(".git")
    clean_branch = branch.strip()

    async with httpx.AsyncClient(timeout=10.0) as client:
        repo_url = f"{GITHUB_API}/repos/{clean_owner}/{clean_repo}"
        try:
            resp = await client.get(repo_url, headers=_headers())
            
            if resp.status_code == 200:
                repo_data = resp.json()
                default_branch = repo_data.get("default_branch", "main")

                # Verify specified branch
                ref_url = f"{GITHUB_API}/repos/{clean_owner}/{clean_repo}/git/ref/heads/{clean_branch}"
                ref_resp = await client.get(ref_url, headers=_headers())
                if ref_resp.status_code == 200:
                    return True, clean_branch, None

                # Fallback to default branch if 'main' was passed but default is different (e.g. 'master')
                if clean_branch == "main" and default_branch != "main":
                    def_ref_url = f"{GITHUB_API}/repos/{clean_owner}/{clean_repo}/git/ref/heads/{default_branch}"
                    def_ref_resp = await client.get(def_ref_url, headers=_headers())
                    if def_ref_resp.status_code == 200:
                        return True, default_branch, None

                return False, clean_branch, f"Branch '{clean_branch}' not found in {clean_owner}/{clean_repo}."

            elif resp.status_code == 404:
                # Private repo or misspelled name - try git ls-remote fallback in case token is set
                ls_ok, detected_branch = await _check_git_ls_remote(clean_owner, clean_repo, clean_branch)
                if ls_ok:
                    return True, detected_branch, None
                return False, clean_branch, f"Repository '{clean_owner}/{clean_repo}' not found or is private."

            elif resp.status_code in (403, 429):
                # Rate limited on REST API - try git ls-remote fallback!
                ls_ok, detected_branch = await _check_git_ls_remote(clean_owner, clean_repo, clean_branch)
                if ls_ok:
                    return True, detected_branch, None
                return False, clean_branch, "GitHub API rate limit reached on backend. Please configure GITHUB_TOKEN in settings."

            else:
                ls_ok, detected_branch = await _check_git_ls_remote(clean_owner, clean_repo, clean_branch)
                if ls_ok:
                    return True, detected_branch, None
                return False, clean_branch, f"GitHub returned status code {resp.status_code}."

        except Exception as e:
            ls_ok, detected_branch = await _check_git_ls_remote(clean_owner, clean_repo, clean_branch)
            if ls_ok:
                return True, detected_branch, None
            return False, clean_branch, f"Failed to reach GitHub: {str(e)}"


async def fetch_repo_tree(owner: str, repo: str, branch: str = "main") -> list[dict]:
    """
    Fetch the full file tree of a repository.
    Returns list of: { path, sha, size, type }
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get the branch HEAD SHA
        ref_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_resp = await client.get(ref_url, headers=_headers())
        
        if ref_resp.status_code == 404:
            raise ValueError(f"Repository {owner}/{repo} or branch {branch} not found.")
        ref_resp.raise_for_status()
        
        commit_sha = ref_resp.json()["object"]["sha"]

        # Get full recursive tree
        tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1"
        tree_resp = await client.get(tree_url, headers=_headers())
        tree_resp.raise_for_status()
        tree_data = tree_resp.json()

        files = []
        for item in tree_data.get("tree", []):
            if item["type"] == "blob":
                ext = os.path.splitext(item["path"])[1].lower()
                if ext in settings.supported_extensions:
                    files.append({
                        "path": item["path"],
                        "sha": item["sha"],
                        "size": item.get("size", 0),
                    })

        return files


async def fetch_file_content_batch(owner: str, repo: str, paths: list[str], branch: str = "main", max_concurrent: int = 100) -> dict[str, str]:
    """
    Fetch multiple files concurrently using a semaphore.
    Returns { path: content }.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def fetch_single(client, path: str):
        async with semaphore:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            try:
                # Need longer timeout for raw content on big repos
                resp = await client.get(url, headers=_headers(), timeout=45.0)
                if resp.status_code == 200:
                    results[path] = resp.text
            except Exception as e:
                print(f"Error fetching {path}: {e}")

    # Use a single client with increased connection limits
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [fetch_single(client, p) for p in paths]
        await asyncio.gather(*tasks)

    return results
