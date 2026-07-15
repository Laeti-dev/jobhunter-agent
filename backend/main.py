from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graphs.chat_graph import graph
from utils.database import init_db
from routers.cv import router as cv_router
from routers.github import router as github_router
from routers.job_offers import router as jobs_router

app = FastAPI()
init_db()
app.include_router(cv_router)
app.include_router(github_router)
app.include_router(jobs_router)

app.add_middleware(
    CORSMiddleware, # Cross-Origin Resource Sharing middleware to allow requests from the frontend
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Receive a user message and return a response from the LLM."""
    messages = request.history + [{"role": "user", "content": request.message}]
    result = graph.invoke({"messages": messages})
    return {"response": result["messages"][-1]["content"]}


