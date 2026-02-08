from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents import run_pipeline
from app.database import log_query, get_overview_stats, get_rep_stats, get_system_stats
from app.rag import get_document_content

router = APIRouter(prefix="/api")


class QueryRequest(BaseModel):
    question: str
    rep_id: str


@router.post("/query")
async def handle_query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not req.rep_id.strip():
        raise HTTPException(status_code=400, detail="Rep ID is required")

    result = run_pipeline(req.question.strip(), req.rep_id.strip())
    log_query(result.to_dict())
    return result.to_dict()


@router.get("/document/{filename}")
async def get_document(filename: str):
    content = get_document_content(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"filename": filename, "content": content}


@router.get("/stats/overview")
async def stats_overview():
    return get_overview_stats()


@router.get("/stats/reps")
async def stats_reps():
    return get_rep_stats()


@router.get("/stats/system")
async def stats_system():
    return get_system_stats()
