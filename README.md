# JobHunter Agent

A learning project built to develop AI Engineer skills (Agentic systems, RAG, Generative AI) while building a practical tool for job hunting assistance.

## Project Goal

Build a full-stack AI-powered assistant that guides users through every step of their job search — from crafting a CV to preparing for interviews. The application pairs a React frontend with a Python backend powered by a LangGraph agent, running open-source LLMs locally via Ollama.

This project is designed for learning: each phase introduces new technical concepts progressively.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React | Chat interface |
| Backend | FastAPI | REST API |
| LLM Router | LiteLLM | Model-agnostic LLM calls |
| LLM (local) | Ollama (Llama 3.2, Mistral…) | Local inference on Apple Silicon |
| Agent Framework | LangGraph | Stateful agent graphs |
| Job Offers API | France Travail API (OAuth2) | Real job postings data source |
| GitHub API | GitHub REST API | Fetch pinned repos for cover letter RAG |
| HTTP Client | httpx | Async API calls to France Travail |
| Embeddings | sentence-transformers (HuggingFace) | Semantic search for RAG |
| Vector Store | ChromaDB | Store and retrieve embeddings (CV + GitHub repos) |
| Database | SQLite | Persist CV data and chat history |
| Model Evaluation | Weave (W&B) | Benchmark LLM outputs against ground-truth criteria |
| Quality Evaluation | DeepEval | LLM-as-a-judge RAG quality metrics (faithfulness, relevancy) |
| Containerisation | Docker | Packaging (added in Phase 3–4) |

---

## Project Phases

### Phase 1 — Simple Chatbot (foundations)
> Skills: FastAPI, React, LiteLLM, LangGraph basics, prompt engineering

- Set up the FastAPI backend and React frontend
- Connect LiteLLM to a local Ollama model
- Build a minimal LangGraph graph (single node) to handle chat
- Create a functional chat UI focused on job hunting topics

The chat interface shows a loading state while the agent processes the request, then renders the final response as formatted markdown.

| Processing | Final response |
|---|---|
| ![Chatbot processing the request](./documentation/img/chatbot-thinking.png) | ![Chatbot final response](./documentation/img/chatbot-response.png) |

### Phase 2 — CV Builder Agent (memory & state)
> Skills: multi-turn conversation, structured outputs, conversation memory, SQLite, HuggingFace models

- The agent asks targeted questions to collect the user's career history
- LangGraph manages conversation state across multiple turns, including conditional routing (`route_to_generate_cv`) to decide when enough information has been collected
- Structured output (Pydantic `CVProfile`) constrains the LLM's final answer into valid JSON, which is then stored in SQLite
- A human-in-the-loop pattern lets the agent propose inferred soft skills, only keeping them if the user confirms
- Benchmark of open-source models (Llama 3.2 vs Qwen 2.5) on CV extraction accuracy using **Weave (W&B)**, comparing hallucination rate and field correctness across models
- End-to-end pipeline working: conversation → `[CV_READY]` → structured extraction (Qwen 2.5) → SQLite persistence → CV preview in the React UI
- **Known limitation** (kept as-is, documented in `documentation/learnings.md`): on long conversations, the small/medium local models occasionally lose track of the system prompt's rules (e.g. skip a section before declaring completion) or residually hallucinate an inferred soft skill — a real capability ceiling of these models rather than a code bug

### Phase 3 — Job Search & RAG Analysis
> Skills: OAuth2 API integration, RAG pipeline, embeddings, semantic search, ChromaDB, qualitative evaluation

Rather than pasting a job posting manually, the app connects to the **France Travail API** (Pôle Emploi) to fetch real job offers matching the user's profile.

- A **Query Builder agent** reads the stored `CVProfile` and generates optimal search parameters (keywords, location via `/referentiel/communes`, experience level)
- User can **validate and adjust** these parameters before launching the search
- The app authenticates with France Travail via **OAuth2 client credentials** (token cached and auto-refreshed)
- Job offers are fetched from `/offres/search` and displayed as selectable cards
- Selecting an offer triggers a **RAG pipeline**: the offer text is embedded with `sentence-transformers`, compared semantically against the stored CV using ChromaDB, and an LLM generates a detailed match analysis (strengths, gaps, suggestions)
- **Qualitative evaluation** with DeepEval: three RAG metrics (contextual relevancy, faithfulness, answer relevancy) measured using a local Ollama model as LLM-as-a-judge

### Phase 4a — Cover Letter with Multi-Source RAG
> Skills: multi-source RAG, GitHub API, prompt chaining, Human-in-the-loop, document generation

Rather than generating a generic cover letter, the app fetches the user's **pinned GitHub repositories** and indexes them alongside the CV, so the letter can cite concrete projects as proof of skills.

- Fetch the user's 6 pinned repos from the **GitHub REST API** (public, no token required)
- Index each repo's README and metadata into a dedicated ChromaDB collection (`github_projects`)
- When an offer is selected, run **two RAG queries in parallel**: one against the CV, one against GitHub repos
- The LLM receives both sets of retrieved chunks to write a cover letter that maps the offer's qualification points to real, verifiable projects
- A **Human-in-the-loop** confirmation step lets the user review before the letter is generated

### Phase 5 — Autonomous Web Agent & Interview Simulation (advanced agentic)
> Skills: tool use, agentic loops, web scraping, multi-agent coordination

- Agent autonomously browses job boards to find relevant postings
- Adapts the CV automatically for each opportunity
- Simulates a job interview based on the posting and the user's profile

---

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry 2+
- Node.js 22+ (use nvm to manage versions)
- Ollama (`brew install ollama`)

### Install a local model

```bash
ollama serve         # start the Ollama server (keep this terminal open)
ollama pull llama3.2 # download the default model
```

### Backend setup

```bash
cd backend
poetry install
poetry run uvicorn main:app --reload
```

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

---

## Running Locally

Once everything above is installed, starting the app requires **3 terminals** running at the same time.

**Terminal 1 — Ollama (LLM server)**
```bash
ollama serve
```

**Terminal 2 — Backend (FastAPI)**
```bash
cd backend
poetry run uvicorn main:app --reload
```
Runs on [http://localhost:8000](http://localhost:8000). Check it's alive: `curl http://localhost:8000/health`.

**Terminal 3 — Frontend (React)**
```bash
cd frontend
npm run dev
```
Runs on [http://localhost:5173](http://localhost:5173) — open this URL in your browser to use the chatbot.

> Start them in this order (Ollama → backend → frontend) so each service finds its dependency already running.

---

## Project Status

- [x] Project planning and architecture design
- [x] Phase 1 — Simple Chatbot
- [x] Phase 2 — CV Builder Agent
- [x] Phase 3 — Job Search & RAG Analysis
- [ ] Phase 4a — Cover Letter with Multi-Source RAG
- [ ] Phase 4b — Market Trends (weekly recap from indexed offers)
- [ ] Phase 5 — Autonomous Web Agent & Interview Simulation
