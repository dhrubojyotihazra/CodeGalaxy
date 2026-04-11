"""
CodeGalaxy Backend - Ingest Router
Handles repository ingestion pipeline execution.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, Repository, FileNode, Edge
from app.models.schemas import IngestRequest, IngestStatusResponse
from app.services import github, parser, embeddings, analyzer, reducer, ingestor, summarizer

router = APIRouter(prefix="/api", tags=["ingest"])


async def _run_pipeline(repo_id: int, owner: str, repo: str, branch: str):
    """
    Parallelized background task for high-speed repository ingestion using local cloning.
    Uses multiple sessions to prevent long-held SQLite locks.
    Limit concurrency to prevent OOM on restricted environments (HFS).
    """
    from app.models.database import async_session
    sem = asyncio.Semaphore(20) # Limit to 20 concurrent intensive tasks

    repo_path = None
    all_paths = []
    files_data = []

    try:
        # 1. Initial Setup & Clone
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.status = "cloning"
            await db.commit()
            github_url = f"https://github.com/{owner}/{repo}.git"
            
        repo_path = await asyncio.to_thread(ingestor.clone_repo, github_url)
        
        # 2. Traversal
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.status = "reading files"
            await db.commit()
        
        files_data = await ingestor.get_source_files(repo_path)
        all_paths = [f["path"] for f in files_data]
        
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.total_files = len(files_data)
            repo_obj.status = "parsing code"
            await db.commit()

        if not files_data:
            async with async_session() as db:
                repo_obj = await db.get(Repository, repo_id)
                repo_obj.status = "error"
                await db.commit()
            return

        # 3. Parallel Parse (with concurrency control)
        async def _bounded_parse(p, c):
            async with sem:
                return await parser.parse_file_async(p, c)

        parse_tasks = [
            _bounded_parse(f["path"], f["content"]) 
            for f in files_data
        ]
        parsed_results = await asyncio.gather(*parse_tasks)
        
        # 4. Save Nodes
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            for i, (f, parsed) in enumerate(zip(files_data, parsed_results)):
                node = FileNode(
                    repo_id=repo_id,
                    path=f["path"],
                    filename=f["path"].split("/")[-1],
                    language=parsed["language"],
                    sha=f["sha"],
                    content=f["content"],
                    loc=parsed["loc"],
                    imports=parsed["imports"],
                    functions=parsed["functions"],
                    classes=parsed["classes"],
                    function_count=len(parsed["functions"]),
                )
                db.add(node)
                repo_obj.processed_files = i + 1
                if (i + 1) % 500 == 0:
                    await db.commit()
                    # Re-get repo_obj after commit because session might expire it
                    repo_obj = await db.get(Repository, repo_id)
            await db.commit()

        # 5. Resolve Imports
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.status = "resolving imports"
            await db.commit()
            
            # Fetch nodes to resolve
            result = await db.execute(select(FileNode).where(FileNode.repo_id == repo_id))
            nodes = result.scalars().all()
            
            for node in nodes:
                source_dir = "/".join(node.path.split("/")[:-1])
                for imp in (node.imports or []):
                    target_path = parser.resolve_import_to_path(imp, all_paths, source_dir)
                    if target_path and target_path != node.path:
                        edge = Edge(
                            repo_id=repo_id,
                            source_path=node.path,
                            target_path=target_path,
                            edge_type="import",
                        )
                        db.add(edge)
            await db.commit()

        # 6. Embeddings Phase
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.status = "embedding vectors"
            await db.commit()
            
            result = await db.execute(select(FileNode).where(FileNode.repo_id == repo_id).where(FileNode.content != None))
            valid_nodes = result.scalars().all()
            
            if valid_nodes:
                contents = [n.content for n in valid_nodes]
                emb_vectors = await embeddings.embed_batch(contents)
                for node, emb in zip(valid_nodes, emb_vectors):
                    node.embedding = emb
                await db.commit()

                # 7. Reducer Phase
                repo_obj = await db.get(Repository, repo_id)
                repo_obj.status = "computing 3D space"
                await db.commit()
                
                valid_embeddings = [n.embedding for n in valid_nodes if n.embedding]
                if valid_embeddings:
                    coords = reducer.reduce_to_3d(valid_embeddings)
                    # Use index map to apply coords
                    nodes_with_emb = [n for n in valid_nodes if n.embedding]
                    for i, node in enumerate(nodes_with_emb):
                        node.x = coords[i]["x"]
                        node.y = coords[i]["y"]
                        node.z = coords[i]["z"]
                    await db.commit()

        # 8. Analysis Phase
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            repo_obj.status = "analyzing code health"
            await db.commit()
            
            result = await db.execute(select(FileNode).where(FileNode.repo_id == repo_id))
            nodes = result.scalars().all()
            
            # Use the same semaphore to limit analysis CPU/Memory usage
            async def _bounded_analyze(c, l, lc, fc, ic):
                async with sem:
                    return await analyzer.analyze_file_async(c, l, lc, fc, ic)

            analysis_tasks = [
                _bounded_analyze(
                    node.content, node.language, node.loc, 
                    node.function_count, len(node.imports or [])
                )
                for node in nodes
            ]
            analysis_results = await asyncio.gather(*analysis_tasks)
            
            for node, res in zip(nodes, analysis_results):
                node.todo_count = res["todo_count"]
                node.complexity = res["complexity"]
                node.risk_score = res["risk_score"]
                # Calculate initial importance score
                node.importance_score = await summarizer.get_importance_score(node.filename, node.content, node.loc)

            await db.commit()

            repo_obj.status = "done"
            await db.commit()

    except Exception as e:
        print(f"Pipeline error for {owner}/{repo}: {e}")
        async with async_session() as db:
            repo_obj = await db.get(Repository, repo_id)
            if repo_obj:
                repo_obj.status = "error"
                await db.commit()
        raise
    finally:
        if repo_path:
            ingestor.cleanup_repo(repo_path)

@router.post("/ingest")
async def ingest_repo(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start ingestion of a GitHub repository."""
    # 1. Quickly validate the repo and branch exist before starting pipeline
    if not await github.check_repo_exists(request.owner, request.repo, request.branch):
        raise HTTPException(
            status_code=404, 
            detail=f"Repository {request.owner}/{request.repo} or branch '{request.branch}' not found. Please check spelling."
        )

    repo = Repository(
        owner=request.owner,
        name=request.repo,
        branch=request.branch,
        status="pending",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    background_tasks.add_task(_run_pipeline, repo.id, request.owner, request.repo, request.branch)

    return {"repo_id": repo.id, "status": "pending", "message": "Ingestion started"}


@router.get("/ingest/{repo_id}/status", response_model=IngestStatusResponse)
async def get_ingest_status(repo_id: int, db: AsyncSession = Depends(get_db)):
    """Get the status of an ingestion job."""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    total = max(repo.total_files, 1)
    return IngestStatusResponse(
        repo_id=repo.id,
        status=repo.status,
        total_files=repo.total_files,
        processed_files=repo.processed_files,
        progress=round(repo.processed_files / total * 100, 1),
    )
