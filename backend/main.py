from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graphs.chat_graph import graph
from graphs.cv_graph import cv_graph
from database import init_db

app = FastAPI()
init_db()

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

@app.post("/cv/chat")
async def cv_chat(request: ChatRequest):
    """Receive a user message and return a response from the LLM."""
    messages = request.history + [{"role": "user", "content": request.message}]
    result = cv_graph.invoke({"messages": messages})
    return {"response": result["messages"][-1]["content"]}
