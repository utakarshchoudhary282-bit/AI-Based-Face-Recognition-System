"""Start here. Run:  uvicorn app.main:app   (from the backend folder), then open http://localhost:8000"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BACKEND_DIR
from .db import SessionLocal, init_db
from .face.embedder import ensure_model
from .rag.index import policy_index
from .routers import admin, auth, employees, knowledge, recognition
from .security import ensure_default_admin

WEBSITE = Path(BACKEND_DIR).parent / "frontend" / "dist"     # the built React app


@asynccontextmanager
async def startup(app: FastAPI):
    init_db()                                   # create tables
    with SessionLocal() as db:
        ensure_default_admin(db)                # first admin login
    ensure_model()                              # download SFace once
    policy_index.ensure()                       # build the policy search index once
    yield


app = FastAPI(title="Employee Verification Portal", lifespan=startup)
for r in (auth.router, employees.router, recognition.router, knowledge.router, admin.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve the React website from the same server: every non-API address returns the app.
if WEBSITE.exists():
    app.mount("/assets", StaticFiles(directory=WEBSITE / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def website(path: str):
        file = WEBSITE / path
        if path and file.is_file() and WEBSITE in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(WEBSITE / "index.html")
