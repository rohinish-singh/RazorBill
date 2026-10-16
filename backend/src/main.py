from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import init_db, seed_default_incidents
from .chatbot import QueryRequest, QueryResponse, process_incident_query


class HealthResponse(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and seed mock records if needed
    init_db()
    seed_default_incidents()
    yield


app = FastAPI(
    title="RazorBill Backend API",
    version="0.1.0",
    description="Live Video Event Summarization, Classification, and Conversational Querying",
    lifespan=lifespan,
)

# CORS configuration for local frontend and teammate integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.post("/api/query", response_model=QueryResponse)
async def query_incidents_endpoint(req: QueryRequest) -> QueryResponse:
    try:
        limit = req.limit if req.limit is not None else 50
        offset = req.offset if req.offset is not None else 0
        return await process_incident_query(req.question, limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(exc)}")
