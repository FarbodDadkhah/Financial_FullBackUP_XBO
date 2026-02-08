from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import BASE_DIR
from app.database import init_db
from app.rag import init_rag
from app.routes_api import router as api_router
from app.routes_pages import router as pages_router


def create_app() -> FastAPI:
    app = FastAPI(title="Customer Service Support System")

    # Initialize database
    init_db()

    # Initialize RAG knowledge base
    chunk_count = init_rag()
    print(f"Knowledge base loaded: {chunk_count} chunks indexed")

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    # Register routes
    app.include_router(api_router)
    app.include_router(pages_router)

    return app
