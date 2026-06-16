# Learnings

## Phase 1 — Simple Chatbot

### FastAPI
- FastAPI is a Python web framework for building REST APIs
- It needs **Uvicorn** (an ASGI server) to receive HTTP requests — FastAPI defines the logic, Uvicorn handles the network
- `@app.get("/route")` and `@app.post("/route")` define endpoints
- **Pydantic BaseModel** automatically validates incoming request data — if a required field is missing, FastAPI returns a clear error
- **CORSMiddleware** is required to allow the React frontend (port 5173) to call the backend (port 8000) — browsers block cross-origin requests by default

### LangGraph
- LangGraph is a framework for building agents as **state graphs** (graphes d'états)
- A graph is made of **nodes** (functions that do something) and **edges** (connections between nodes)
- The **State** is a shared typed dictionary passed between all nodes — it holds the conversation history
- The simplest graph: `START → chat_node → END`
- `StateGraph` → `add_node` → `add_edge` → `compile()` is the standard build pattern

### LiteLLM
- LiteLLM is a **model-agnostic router** — same Python code works with any LLM provider
- Syntax: `completion(model="ollama/llama3.2", messages=[...])`
- Changing the model string is all it takes to switch providers (Ollama, HuggingFace, Anthropic, etc.)

### Ollama
- Ollama runs open-source LLMs locally on Apple Silicon (M4 Pro) using the Neural Engine
- Must be started with `ollama serve` before use
- Models are downloaded with `ollama pull <model-name>`
- LiteLLM connects to Ollama with the prefix `ollama/`

### React (frontend)
- `useState` manages local component state — `messages` (conversation history) and `input` (current text)
- `fetch` sends HTTP POST requests to the FastAPI backend
- An `isLoading` state disables the send button and shows a "typing" indicator while waiting for the LLM
- **Tailwind CSS v4** with Vite: install `@tailwindcss/vite`, add the plugin to `vite.config.js`, add `@import "tailwindcss"` to `index.css` — no config file needed

### Tooling lessons
- Poetry and Homebrew can install multiple Python versions — always set the correct one with `poetry env use /path/to/python3.12`
- Node.js version matters: Vite 6 requires Node 20.19+ or 22+ — use **nvm** to manage Node versions cleanly
- `nvm install 22 && nvm use 22` upgrades Node without breaking other projects
- When npm optional dependencies fail to install (rolldown binding issue), delete `node_modules` and `package-lock.json` then reinstall
