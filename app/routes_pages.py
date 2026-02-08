from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from app.rag import get_document_content

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("rep.html", {"request": request})


@router.get("/rep", response_class=HTMLResponse)
async def rep_view(request: Request):
    return templates.TemplateResponse("rep.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/document/{filename}", response_class=HTMLResponse)
async def document_view(request: Request, filename: str):
    content = get_document_content(filename)
    if content is None:
        return HTMLResponse("<h1>Document not found</h1>", status_code=404)
    return templates.TemplateResponse(
        "document.html",
        {"request": request, "filename": filename, "content": content},
    )
