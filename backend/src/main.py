from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


app = FastAPI(
    title="RazorBill Backend API",
    version="0.1.0",
    description="Live Video Event Summarization, Classification, and Conversational Querying",
)


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="healthy")

