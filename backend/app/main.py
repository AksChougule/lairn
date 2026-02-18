from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.quiz import router as quiz_router
from app.db.session import create_db_and_tables
from app.llm.ollama import ollama_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Liarn API", lifespan=lifespan)
app.include_router(quiz_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, object]:
    reachable, model = ollama_client.check_health()
    return {"status": "ok", "ollama": {"reachable": reachable, "model": model}}
