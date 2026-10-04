"""
CodeGalaxy Backend - Files Router
Returns detailed file information for the side panel.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import httpx
import time
from app.config import settings

from app.models.database import get_db, FileNode, Edge
from app.models.schemas import FileDetailResponse

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files/{file_id}", response_model=FileDetailResponse)
async def get_file_detail(file_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific file node."""
    file_node = await db.get(FileNode, file_id)
    if not file_node:
        raise HTTPException(status_code=404, detail="File not found")

    # Compute Fan-In (files that import this one)
    fan_in_query = select(func.count(Edge.id)).where(
        Edge.repo_id == file_node.repo_id,
        Edge.target_path == file_node.path
    )
    fan_in = await db.scalar(fan_in_query)

    # Compute Fan-Out (files this one imports)
    fan_out_query = select(func.count(Edge.id)).where(
        Edge.repo_id == file_node.repo_id,
        Edge.source_path == file_node.path
    )
    fan_out = await db.scalar(fan_out_query)

    return FileDetailResponse(
        id=file_node.id,
        path=file_node.path,
        filename=file_node.filename,
        language=file_node.language,
        content=file_node.content,
        loc=file_node.loc,
        complexity=round(file_node.complexity, 2),
        risk_score=file_node.risk_score,
        todo_count=file_node.todo_count,
        function_count=file_node.function_count,
        imports=file_node.imports or [],
        functions=file_node.functions or [],
        classes=file_node.classes or [],
        fan_in=fan_in or 0,
        fan_out=fan_out or 0,
    )

_cached_groq_models: list[str] = []
_groq_cache_timestamp: float = 0.0

async def _get_active_groq_models(api_key: str) -> list[str]:
    """
    Dynamically discover all active models directly from Groq API.
    Auto-ranks coding/chat models and filters out non-chat models.
    Caches for 15 minutes to preserve sub-second response times.
    """
    global _cached_groq_models, _groq_cache_timestamp
    now = time.time()
    if _cached_groq_models and (now - _groq_cache_timestamp < 900):
        return _cached_groq_models

    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            if resp.status_code == 200:
                raw_ids = [m["id"] for m in resp.json().get("data", [])]
                # Filter out audio, whisper, prompt guard, vision/rerank
                chat_models = [
                    m_id for m_id in raw_ids 
                    if not any(x in m_id.lower() for x in ["whisper", "guard", "orpheus", "embed", "rerank"])
                ]
                
                def rank_score(m: str) -> int:
                    ml = m.lower()
                    if "qwen" in ml: return 100
                    if "llama-3.3" in ml: return 95
                    if "llama-3.1" in ml: return 90
                    if "deepseek" in ml: return 85
                    if "gpt-oss-120b" in ml: return 80
                    if "gpt-oss" in ml: return 75
                    if "llama" in ml: return 70
                    return 20

                sorted_models = sorted(chat_models, key=rank_score, reverse=True)
                if sorted_models:
                    _cached_groq_models = sorted_models
                    _groq_cache_timestamp = now
                    return _cached_groq_models
        except Exception as e:
            print(f"Dynamic Groq model discovery exception: {e}")

    # Fallback list if discovery fails
    return _cached_groq_models or ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]


async def _call_llm_summary(path: str, code_snippet: str) -> str:
    """Helper to request AI architectural summary with multi-model fallback."""
    global _cached_groq_models, _groq_cache_timestamp
    prompt = f"""You are a senior software architect. Provide a concise, 2-3 sentence plain-English summary explaining the primary purpose of this file.
Analyze its logic to understand its role. Do NOT list the functions. Explain *why* it exists.

File path: {path}
Code:
```
{code_snippet[:8000]}
```
"""

    # 1. Try Groq with dynamic auto-discovered active models
    if settings.groq_api_key:
        active_models = await _get_active_groq_models(settings.groq_api_key)
        
        # User configured model takes precedence if set, followed by auto-discovered active models
        models_to_try = []
        if settings.groq_model:
            models_to_try.append(settings.groq_model)
        for m in active_models:
            if m not in models_to_try:
                models_to_try.append(m)

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            for model_id in models_to_try:
                try:
                    payload = {
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": "You provide extremely clear, concise architectural intuition about code files."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 150
                    }
                    resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        summary = data["choices"][0]["message"]["content"].strip()
                        if summary:
                            return summary
                    elif resp.status_code == 404:
                        # Model was deprecated or removed by Groq!
                        # Invalidate cache so next request queries Groq's live model catalog
                        _cached_groq_models = []
                        _groq_cache_timestamp = 0.0
                        continue
                    else:
                        print(f"Groq API error ({model_id}): {resp.status_code} - {resp.text}")
                except Exception as e:
                    print(f"Groq call exception ({model_id}): {e}")

    # 2. Try OpenRouter fallback
    if settings.openrouter_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": "You provide extremely clear, concise architectural intuition about code files."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 150
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    summary = data["choices"][0]["message"]["content"].strip()
                    if summary:
                        return summary
        except Exception as e:
            print(f"OpenRouter fallback error: {e}")

    # 3. Try OpenAI fallback
    if settings.openai_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You provide extremely clear, concise architectural intuition about code files."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 150
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    summary = data["choices"][0]["message"]["content"].strip()
                    if summary:
                        return summary
        except Exception as e:
            print(f"OpenAI fallback error: {e}")

    if not (settings.groq_api_key or settings.openrouter_api_key or settings.openai_api_key):
        return "Please set GROQ_API_KEY in Space secrets to enable AI summaries."

    return "STATION_UPLINK_FAILURE: AI analysis service currently unavailable. Please verify API key in settings."


@router.post("/files/{file_id}/summary")
async def generate_file_summary(file_id: int, db: AsyncSession = Depends(get_db)):
    """Generate a brief 2-3 sentence summary of the file using LLM API."""
    file_node = await db.get(FileNode, file_id)
    if not file_node:
        raise HTTPException(status_code=404, detail="File not found")

    if not file_node.content:
        return {"summary": "No raw code available for this file."}

    summary = await _call_llm_summary(file_node.path, file_node.content)
    return {"summary": summary}


@router.post("/ai/summarize-code")
async def summarize_raw_code(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Proxy endpoint to generate summary for raw code without a DB file ID."""
    code = data.get("code", "")
    path = data.get("path", "unknown")
    if not code:
        return {"summary": "No code provided for analysis."}

    summary = await _call_llm_summary(path, code)
    return {"summary": summary}
