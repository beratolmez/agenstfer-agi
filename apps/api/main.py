import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure modules can be imported
sys.path.insert(0, os.path.abspath("apps/services/rag"))
sys.path.insert(0, os.path.abspath("apps/services/ai-agent"))

try:
    from ai_agent.graph import create_graph
    from rag_service.ingest import ingest_markdown_file
except ImportError as e:
    print(f"Warning: Could not import agent modules: {e}")

app = FastAPI(title="AGI Server API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str


class SetupRequest(BaseModel):
    files: list[str]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/setup")
def run_setup(req: SetupRequest):
    """Triggers the RAG ingestion for the setup wizard."""
    try:
        results = []
        for file in req.files:
            file_path = os.path.join(os.getcwd(), file)
            if os.path.exists(file_path):
                ingest_markdown_file(file_path)
                results.append(f"Ingested {file}")
            else:
                results.append(f"File not found: {file}")
        return {"message": "Setup complete", "details": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Runs the multi-agent pipeline."""
    try:
        graph = create_graph()
        result = graph.invoke({"messages": [req.query]})

        return {
            "research_data": result.get("research_data", ""),
            "analysis_data": result.get("analysis_data", ""),
            "final_review": result.get("messages", [""])[-1] if result.get("messages") else "",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Mount frontend
frontend_path = os.path.join(os.getcwd(), "apps", "web", "dist")
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
