"""
CodeGalaxy Backend - High-Speed local Ingestor
Uses GitPython to clone repositories and traverse them locally.
"""
import os
import shutil
import tempfile
import asyncio
from git import Repo
from app.config import settings

def clone_repo(github_url: str, branch: Optional[str] = None) -> str:
    """
    Clones a GitHub repository to a temporary directory.
    Uses the GITHUB_TOKEN from settings for authentication.
    """
    temp_dir = tempfile.mkdtemp(prefix="codegalaxy_")
    
    # Inject token if available for private/rate-limited repos
    clone_url = github_url
    if settings.github_token:
        # Expected github_url format: https://github.com/owner/repo.git
        if github_url.startswith("https://github.com/"):
            clone_url = github_url.replace("https://github.com/", f"https://{settings.github_token}@github.com/")

    try:
        kwargs = {"depth": 1}
        if branch:
            kwargs["branch"] = branch
        Repo.clone_from(clone_url, temp_dir, **kwargs)
        return temp_dir
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        # Scrub token from error message for security
        err_msg = str(e).replace(settings.github_token, "REDACTED_TOKEN") if settings.github_token else str(e)
        raise RuntimeError(f"Failed to clone repository: {err_msg}")

async def get_source_files(repo_path: str):
    """
    Traverses the cloned repository and returns file data.
    Uses aggressive filtering and hierarchical grouping for the Galaxy view.
    """
    source_files = []
    
    # Aggressive ignore lists from teammate's version
    ignore_dirs = {
        '.git', '.github', 'node_modules', 'venv', 'env', 
        '__pycache__', 'dist', 'build', 'public', 'assets', 
        '.next', 'target', '.idea', '.vscode'
    }
    ignore_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
        '.mp4', '.pdf', '.zip', '.tar', '.gz', '.exe', 
        '.dll', '.so', '.woff', '.woff2', '.ttf', '.eot'
    }
    
    # Supported extensions from app settings
    supported = set(settings.supported_extensions)

    def _sync_walk():
        files_data = []
        for root, dirs, files in os.walk(repo_path):
            # Prune ignore_dirs in-place to prevent os.walk from descending
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ignore_extensions:
                    continue
                if ext not in supported:
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace("\\", "/")
                
                try:
                    # Content capping to 10KB as per teammate's tech
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000) 
                    
                    files_data.append({
                        "path": rel_path,
                        "content": content,
                        "size": os.path.getsize(full_path),
                        "sha": "local_import" # We don't need real SHA for local clone
                    })
                except Exception as e:
                    print(f"Skipping {rel_path} due to error: {e}")
                    
        return files_data

    return await asyncio.to_thread(_sync_walk)

def cleanup_repo(repo_path: str):
    """Removes the temporary repository directory."""
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)
