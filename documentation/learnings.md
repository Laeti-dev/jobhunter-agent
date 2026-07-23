# Learnings

## Phase 1 — Simple Chatbot

### FastAPI

- FastAPI is a Python web framework for building REST APIs
- It needs **Uvicorn** (an ASGI server) to receive HTTP requests — FastAPI defines the logic, Uvicorn handles the network
- `@app.get("/route")` and `@app.post("/route")` define endpoints
- **Pydantic BaseModel** automatically validates incoming request data — if a required field is missing, FastAPI returns a clear error
- **CORSMiddleware** is required to allow the React frontend (port 5173) to call the backend (port 8000) — browsers block cross-origin requests by default

### LangGraph

LangGraph lets you build agents as **state graphs** (graphes d'états): a set of nodes (functions) connected by edges (transitions), all sharing a common state.

---

#### 1. The State — shared memory between all nodes

```python
from typing import TypedDict, List

class State(TypedDict):
    messages: List[dict]
```

- `TypedDict` is a standard Python type that defines a dictionary with fixed keys and types
- `State` is the **single source of truth** passed between every node in the graph
- Here it holds `messages`: a list of `{"role": "...", "content": "..."}` dicts — the conversation history
- Every node receives the current state and returns an updated version of it

---

#### 2. The Node — a function that does one thing

```python
from litellm import completion

def chat_node(state: State) -> State:
    """Call the LLM with the current conversation history."""
    response = completion(
        model="ollama/llama3.2",
        messages=state["messages"],   # full conversation history sent to the LLM
    )
    assistant_message = {
        "role": "assistant",
        "content": response.choices[0].message.content,  # extract the text from the response
    }
    return {"messages": state["messages"] + [assistant_message]}  # return updated state
```

- A node is just a **Python function** that takes `State` and returns an updated `State`
- `state["messages"]` gives the full conversation history so the LLM has context
- `response.choices[0].message.content` is the LiteLLM response format (same as OpenAI API)
- The node returns a new state with the assistant's message appended — it never mutates in place

---

#### 3. The Graph — wiring nodes together

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)        # create a graph that uses our State type
builder.add_node("chat", chat_node)  # register the node under the name "chat"
builder.add_edge(START, "chat")    # the graph starts by going to "chat"
builder.add_edge("chat", END)      # after "chat", the graph ends

graph = builder.compile()          # compile into an executable graph
```

- `StateGraph(State)` creates a graph and tells it what shape the state has
- `add_node("name", function)` registers a node — the name is used for edges
- `add_edge(A, B)` means "after node A, go to node B"
- `START` and `END` are special built-in markers for the entry and exit points
- `compile()` validates the graph and returns a runnable object

In Phase 1, the graph is a straight line:
```
START → chat → END
```

In later phases, we will add branches and loops:
```
START → collect_info → [enough info?] → yes → generate_cv → END
                                      → no  → ask_question → collect_info (loop)
```

---

#### 4. Running the graph

```python
result = graph.invoke({"messages": [{"role": "user", "content": "Help me with my CV"}]})
last_message = result["messages"][-1]["content"]
```

- `invoke()` runs the graph from START to END with the given initial state
- It returns the **final state** after all nodes have run
- `result["messages"][-1]` is the last message added — the assistant's response

---

#### 5. How it connects to FastAPI

```
React (fetch POST /chat)
    ↓
FastAPI receives { message, history }
    ↓
Rebuilds the messages list:
    messages = history + [{"role": "user", "content": message}]
    ↓
graph.invoke({"messages": messages})
    ↓
LangGraph runs chat_node → LiteLLM → Ollama (Llama 3.2)
    ↓
Returns { "response": result["messages"][-1]["content"] }
    ↓
React displays the assistant message
```

The full endpoint in `main.py`:

```python
@app.post("/chat")
def chat(request: ChatRequest):
    messages = request.history + [{"role": "user", "content": request.message}]
    result = graph.invoke({"messages": messages})
    return {"response": result["messages"][-1]["content"]}
```

---

### LiteLLM

- LiteLLM is a **model-agnostic router** — same Python code works with any LLM provider
- Syntax: `completion(model="ollama/llama3.2", messages=[...])`
- Changing the model string is all it takes to switch providers:

```python
# Local model via Ollama
completion(model="ollama/llama3.2", messages=[...])

# HuggingFace cloud model
completion(model="huggingface/mistral-7b-instruct", messages=[...])

# Anthropic Claude (requires API key)
completion(model="claude-sonnet-4-6", messages=[...])
```

- The `messages` format follows the **OpenAI standard**: a list of `{"role": "user"/"assistant"/"system", "content": "..."}`
- LiteLLM translates this format for each provider internally

---

### Ollama

- Ollama runs open-source LLMs locally on Apple Silicon (M4 Pro) using the Neural Engine
- Must be started with `ollama serve` before use
- Models are downloaded with `ollama pull <model-name>`
- LiteLLM connects to Ollama with the prefix `ollama/`

---

### React (frontend)

- `useState` manages local component state — `messages` (conversation history) and `input` (current text)
- `fetch` sends HTTP POST requests to the FastAPI backend
- An `isLoading` state disables the send button and shows a "typing" indicator while waiting for the LLM
- **Tailwind CSS v4** with Vite: install `@tailwindcss/vite`, add the plugin to `vite.config.js`, add `@import "tailwindcss"` to `index.css` — no config file needed

---

---

## Phase 2 (WIP) — CV Builder Agent

### Conditional edges — letting the graph decide where to go

Unlike Phase 1's straight line (`START → chat → END`), a conditional edge lets the graph **choose the next node dynamically** based on the state:

```python
def route_to_generate_cv(state: CVState) -> str:
    """Decide whether to generate the CV now or wait for the next user message."""
    last_message = state["messages"][-1]["content"]
    return "generate_cv" if "[CV_READY]" in last_message else END

builder.add_conditional_edges("agent", route_to_generate_cv)
```

- The routing function returns either a **node name** (string) or `END`
- If it returned something else (e.g. a boolean), `add_conditional_edges` needs a third argument: a `path_map` dict translating each possible return value to a node name. Returning the node name directly avoids that extra layer.

### Letting the LLM self-determine completion

Instead of manually tracking "which CV section is filled" in code, the agent's system prompt asks the LLM to add a marker (`[CV_READY]`) when it judges it has enough information. This is simpler to build, at the cost of giving up fine-grained control — a common trade-off in agent design.

### Structured output ≠ truthful output

`response_format=CVProfile` (a Pydantic model) **guarantees the JSON shape** — every field will be present and correctly typed. It does **not** guarantee the LLM only reports what the user actually said. In testing, Llama 3.2 invented soft skills ("Leadership", "Team Management") that were never mentioned, and confused fields (tech skills landed in `spoken_languages`). These are two separate problems:
- **Format correctness** → solved by Pydantic / `response_format`
- **Factual correctness** → depends entirely on prompt quality and model capability

### Human-in-the-loop to turn hallucination into a feature

Rather than only suppressing the LLM's tendency to infer things (e.g. soft skills from experience), the system prompt now tells it to **propose** the inference as a question and only keep it if the user confirms it explicitly:

```
Après avoir recueilli une expérience professionnelle, tu peux déduire des soft
skills probables... propose-les explicitement... et ne les retiens QUE si
l'utilisateur les confirme ou les corrige.
```

This is the human-in-the-loop pattern: the model's inference becomes a suggestion the user validates, not an unchecked assertion.

### Small open-source models hit real limits

Even after tightening the prompt, Llama 3.2 (likely the 3B variant) still hallucinated a refused soft skill and misplaced fields. This isn't a code bug — it's a capability ceiling of small models on nuanced instruction-following ("don't include what the user explicitly declined"). Prompt engineering can only compensate so much; sometimes the fix is a bigger/better model for that specific task.

### Long conversation history breaks rule-following — and the architectural fix

After adding explicit rules to `SYSTEM_PROMPT` ("only emit `[CV_READY]` once all 6 sections have been covered"), the agent still cut the conversation short after the experience section. This is the "lost in the middle" problem: small/medium open-source models lose track of early instructions as the conversation grows — not a bug in the code, but a capability ceiling of the model.

**The real fix: section-based context isolation**

Instead of one continuous context that grows forever, the conversation is split into short-lived contexts — one per section (or even one per item in list-type sections). The graph manages section transitions in code (deterministically), and the LLM only ever sees a short, focused prompt:

```
Phase 2 v1 (wrong): one long chat history → LLM tries to track everything → fails
Phase 2 v2 (fixed): short context per section/item → LLM has one focused task → succeeds
```

**New graph structure (loop with section-level state machine):**

```
START → route_entry
  if flat section (identity, skills, languages):
    ask_in_section → [SECTION_DONE?] → extract_section → advance → next section
  if list section (experiences, education, projects):
    ask_in_item → [ITEM_DONE?] → extract_item → ask_continue → [user answers yes/no]
      → yes: reset item context, ask_in_item again (new item)
      → no:  merge items into collected_data, advance to next section
```

**New state fields (in `CVState`):**

```python
class CVState(TypedDict):
    section_index: int           # which section we're on (0–5)
    context_messages: List[dict] # short context, reset for each section/item
    current_items: List[dict]    # items accumulated for current list section
    collected_data: dict         # data already extracted (never re-sent to the LLM)
    awaiting_continue: bool      # are we waiting for a yes/no answer?
    wants_more_items: bool       # used to route after continue decision
    cv_data: str | None
    cv_id: int | None
```

### LangGraph Checkpointer — stateful agents without client-side state

With per-section context, the state can no longer be carried round-trip via a `history` field — it's too complex. Instead, LangGraph's built-in **checkpointer** system persists the full graph state between HTTP calls, identified by a `thread_id` (generated on the first message, returned to the client, echoed back on each subsequent call):

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

_conn = sqlite3.connect("cv_sessions.db", check_same_thread=False)
checkpointer = SqliteSaver(_conn)
cv_graph = builder.compile(checkpointer=checkpointer)
```

On the API side, state is loaded, the new user message is appended, and the graph is invoked:

```python
config = {"configurable": {"thread_id": thread_id}}
snapshot = cv_graph.get_state(config)
current_state = snapshot.values or DEFAULT_CV_STATE

updated_context = current_state["context_messages"] + [{"role": "user", "content": request.message}]
result = cv_graph.invoke({**current_state, "context_messages": updated_context}, config=config)
```

- `SqliteSaver` requires a direct `sqlite3` connection — `SqliteSaver.from_conn_string()` returns a context manager (not usable directly) in version 3.x
- `check_same_thread=False` is required because FastAPI runs in async threads

### Per-section configuration in `sections.py`

Each section is described as a dict with its instructions, model, and minimum expected exchanges:

```python
SECTIONS = [
    {
        "key": "identity",
        "label": "Identité",
        "is_list": False,
        "model": Identity,
        "min_user_messages": 5,   # guard: 5 fields → at least 5 user turns required
        "instructions": "Collecte ces 5 informations : nom, email, téléphone, ville, métier recherché...",
    },
    {
        "key": "experiences",
        "label": "expérience professionnelle",
        "is_list": True,
        "item_model": Experience,
        "min_user_messages": 4,   # per item: needs poste, entreprise, dates, missions
        "instructions": "Pose des questions sur CETTE expérience (une seule à la fois)...",
    },
    ...
]
```

### Deterministic guards against premature marker detection

The routing functions check two conditions before allowing a section/item to complete — both must be true:

```python
def route_after_section_question(state: CVState) -> str:
    section = SECTIONS[state["section_index"]]
    last_message = state["context_messages"][-1]["content"]
    min_messages = section.get("min_user_messages", 2)
    user_count = sum(1 for m in state["context_messages"] if m["role"] == "user")
    if "[SECTION_DONE]" in last_message and user_count >= min_messages:
        return "extract_section"
    return END
```

1. The LLM must have emitted the marker (`[SECTION_DONE]` or `[ITEM_DONE]`)
2. The minimum number of user messages for this section must have been reached

This is deterministic code that the LLM cannot circumvent by "deciding early."

### Stop sequences — preventing self-continuation

Even with explicit prompt instructions ("STOP after your question"), small models frequently simulate the user's next reply inline (`### User: [invented answer] ### Assistant: next question`). This is cured by a **stop sequence**: the completion call terminates the moment the model starts generating a user turn marker.

```python
response = completion(
    model=model,
    messages=messages,
    temperature=0.2,
    stop=["### User:", "\nUser:", "\nUtilisateur:", "\n### "],
)
```

Stop sequences are deterministic and enforced by the inference engine — unlike prompt instructions, the model cannot "ignore" them.

### Deterministic nodes (no LLM call)

Not every node needs a LLM. `ask_continue_node` generates a fixed question ("Voulez-vous ajouter une autre expérience ?") and `handle_continue_answer_node` classifies the user's reply using keyword matching — zero hallucination risk for these control-flow decisions:

```python
NEGATIVE_KEYWORDS = ["non", "no", "c'est tout", "rien d'autre"]
AFFIRMATIVE_KEYWORDS = ["oui", "yes", "encore", "ajouter"]

def is_affirmative(text: str) -> bool:
    text = text.lower()
    if any(kw in text for kw in NEGATIVE_KEYWORDS):
        return False
    return any(kw in text for kw in AFFIRMATIVE_KEYWORDS)
```

The general principle: **let the LLM do language tasks; let deterministic code do control-flow decisions.**

### Avoiding circular imports across files

Splitting node functions (`nodes/generate_cv_node.py`) from graph wiring (`graphs/cv_graph.py`) created a circular import: the node needed `CVState` from the graph file, and the graph file needed the node function. Fix: move shared types (`BaseState`, `CVState`) into a dependency-free module (`graphs/state.py`) that both other files import from — no file needs to import from the other.

```
graphs/state.py            (depends on nothing)
        ↑                          ↑
nodes/generate_cv_node.py   graphs/cv_graph.py
```

### Testing a node in isolation

Instead of testing through curl with a growing conversation history, a node can be called directly with a hand-crafted fake state — much faster for checking one specific behavior (e.g. does `response_format` actually return valid JSON with Ollama):

```python
from nodes.extract_item_node import extract_item_node
fake_state = {
    "section_index": 1,  # experiences
    "context_messages": [
        {"role": "user", "content": "J'étais cheffe de rang chez Le Bistrot, 2019–2024"},
    ],
    "current_items": [],
    "collected_data": {},
    "awaiting_continue": False,
    "wants_more_items": False,
    "cv_data": None,
    "cv_id": None,
}
result = extract_item_node(fake_state)
print(result["current_items"])
```

### TypedDict does not support default values

```python
class CVState(BaseState):
    cv_data: str | None = None  # raises TypeError at class definition time
```

Unlike Pydantic's `BaseModel`, `TypedDict` fields cannot have default values — only type annotations (`cv_data: str | None`). Defaults must be set when constructing the initial state dict, not in the type definition.

### Benchmarking models with Weave (W&B)

Because LiteLLM makes the model just a string parameter, swapping models for a benchmark is trivial — `generate_cv_node` now accepts a `model` argument instead of hardcoding `"ollama/llama3.2"`.

**Weave** structures a benchmark around three pieces:
- a **dataset**: test cases (conversation + ground-truth expectations)
- **scorers**: functions that check the output against that ground truth (`@weave.op()` decorated)
- an **Evaluation**: runs every model against the dataset through the scorers, logged to a web dashboard

```python
@weave.op()
def no_forbidden_soft_skills(output: str, forbidden_soft_skills: list[str]) -> dict:
    cv_data = json.loads(output)
    soft_skills = [s.lower() for s in (cv_data.get("soft_skills") or [])]
    found = [f for f in forbidden_soft_skills if f.lower() in soft_skills]
    return {"passed": len(found) == 0, "hallucinated_skills": found}

evaluation = weave.Evaluation(dataset=dataset, scorers=[no_forbidden_soft_skills, ...])
await evaluation.evaluate(model_function)
```

- Weave matches dataset dict keys to the scorer's and model function's parameter names automatically
- `weave.init("project-name")` + `WANDB_API_KEY` in `.env` (loaded via `load_dotenv()`) connects the run to a free W&B dashboard
- Environment variable names read by SDKs are case-sensitive by convention — `WANDB_API_KEY`, not `wandb_api_key`

### End-to-end pipeline test (full graph, real conversation)

Running the whole graph (`agent → generate_cv → save_to_db`) with a complete fake conversation confirmed the pipeline works mechanically: the agent emitted `[CV_READY]`, `generate_cv_node` produced valid JSON, and `save_to_db_node` wrote a row to SQLite (`cv_id` returned, incrementing on each run). Swapping the extraction model from Llama 3.2 to Qwen 2.5:7b visibly improved output quality (no phantom experiences, correct field placement).

### Prompt engineering has a ceiling — even with explicit rules

After hardening `generate_cv_node`'s system prompt with an explicit rule ("only include a soft skill if the user confirmed it, otherwise return an empty list"), re-running the **same** conversation through the **same** model twice produced two different sets of hallucinated soft skills (`["Leadership", "Team Management", ...]` once, `["gouvernance", "gestion", "formation"]` another time) — neither matching what was actually confirmed. Two separate causes:
- **Non-determinism**: without a low `temperature`, the same prompt can yield different outputs across runs
- **Limited instruction-following**: explicit negative constraints ("don't add anything beyond X") are harder for models to respect reliably than positive ones ("extract X")

This is a case where prompt engineering alone has diminishing returns — a fully robust fix would require deterministic post-processing (e.g. verifying each soft skill appears verbatim in the conversation) rather than trusting the LLM's judgment at generation time. Documented here as a known limitation to revisit during Phase 4's evaluation work, rather than a bug to chase indefinitely now.

### `temperature` — controlling randomness

```python
completion(model=model, messages=messages, response_format=CVProfile, temperature=0.1)
```

- `temperature` ranges roughly 0–2: `0` ≈ deterministic (always the most likely token), higher values ≈ more varied/creative
- For factual extraction tasks (like filling a structured CV), a low value (e.g. `0.1`) trades creativity for consistency — the opposite of what you'd want for, say, creative writing

### Tooling lessons

- Poetry and Homebrew can install multiple Python versions — always set the correct one with `poetry env use /path/to/python3.12`
- Node.js version matters: Vite 6 requires Node 20.19+ or 22+ — use **nvm** to manage Node versions cleanly
- `nvm install 22 && nvm use 22` upgrades Node without breaking other projects
- When npm optional dependencies fail to install (rolldown binding issue), delete `node_modules` and `package-lock.json` then reinstall

---

## Phase 3 — RAG Pipeline (Retrieval-Augmented Generation)

### What is RAG?

RAG stands for **Retrieval-Augmented Generation**: we *retrieve* relevant information from a knowledge base, then *inject* it as context into the LLM so it can *generate* a grounded, accurate response.

Without RAG, the LLM only knows what it learned during training.
With RAG, we hand it specific documents to read **at query time**.

```
Question: "Does this CV match this job offer?"
              ↓
[Retrieval]   Which parts of the CV are most relevant to this offer?
              ↓
[Augmented]   Send to LLM: the offer + the most relevant CV sections
              ↓
[Generation]  LLM generates a structured analysis: strengths, gaps, suggestions
```

---

### Step 1 — Semantic vectorisation (embeddings)

The core idea: transform text into **numeric vectors** (lists of numbers) so that texts with the same *meaning* have vectors that are close together in mathematical space.

```
"Python, FastAPI, LangGraph"      →  [0.23, -0.71, 0.08, 0.45, ...]  (384 numbers)
"Python backend developer"        →  [0.21, -0.69, 0.11, 0.43, ...]  ← close!
"Chef, pastry, kitchen"           →  [-0.54, 0.33, -0.62, 0.12, ...]  ← far!
```

These vectors are produced by a specialised **embedding model** — in this project, `paraphrase-multilingual-MiniLM-L12-v2` from HuggingFace, which understands French.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
vector = model.encode("Data Scientist Python machine learning")
# → array([0.23, -0.71, 0.08, ...])  with 384 dimensions
```

**Why is this powerful?** Because semantic similarity (*meaning*) is captured, not just exact word matches. "Developer" and "Software Engineer" will have close vectors even if they share no words.

---

### Step 2 — What gets vectorised from the CV

The CV is not vectorised as a single text blob — it is split into **chunks**, one per meaningful section. Each chunk is vectorised separately.

```python
# In utils/rag.py → _chunk_profile() method
def _chunk_profile(self, profile: CVProfile) -> list[dict]:
    chunks = []

    # One chunk per section:
    chunks.append({"id": "summary", "section": "Summary",
                   "text": profile.summary})

    chunks.append({"id": "target_role", "section": "Target role",
                   "text": f"Target role: {profile.target_role}"})

    for i, exp in enumerate(profile.experiences):
        text = f"{exp.title} at {exp.company}. " + ". ".join(exp.achievements)
        chunks.append({"id": f"exp_{i}", "section": "Experience", "text": text})

    chunks.append({"id": "tech_skills", "section": "Technical skills",
                   "text": "Skills: " + ", ".join(profile.tech_skills)})

    # ... also education, projects, soft skills
    return chunks
```

**Why split?** Because a job offer rarely needs the whole CV at once. It looks for specific skills, or a specific type of experience. By splitting, we can retrieve exactly the CV section that best matches the offer.

---

### Step 3 — Storage in ChromaDB

ChromaDB is a **vector database** (vector store): it stores vectors and can search them by similarity very quickly.

```python
# In utils/rag.py → index_cv() method
def index_cv(self, profile: CVProfile) -> None:
    chunks = self._chunk_profile(profile)

    # 1. Delete the old index (in case the CV was updated)
    try:
        self.client.delete_collection("cv_index")
    except Exception:
        pass

    # 2. Create a fresh collection
    self._collection = self.client.create_collection("cv_index")

    # 3. Encode all texts into vectors in one batch (more efficient)
    texts = [c["text"] for c in chunks]
    embeddings = self.model.encode(texts).tolist()

    # 4. Store: vectors + original texts + metadata
    self._collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,       # the numeric vectors
        documents=texts,             # the original texts (to retrieve later)
        metadatas=[{"section": c["section"]} for c in chunks],  # labels
    )
```

Concretely, ChromaDB stores in `./chroma_db/` (persistent on disk) a table like:

| id | section | text | vector |
|---|---|---|---|
| `summary` | Summary | "I am a Data Scientist..." | [0.23, -0.71, ...] |
| `exp_0` | Experience | "AI engineer at LG Electronics..." | [0.41, -0.55, ...] |
| `tech_skills` | Technical skills | "Python, FastAPI, LangGraph..." | [0.18, -0.80, ...] |

---

### Step 4 — Retrieval

When a job offer arrives, its text is vectorised the same way, then ChromaDB is asked: "which CV vectors are closest to this vector?"

```python
# In utils/rag.py → retrieve() method
def retrieve(self, query_text: str, n_results: int = 3) -> list[dict]:
    # 1. Vectorise the job offer text
    query_embedding = self.model.encode([query_text]).tolist()

    # 2. Find the n closest chunks in ChromaDB
    results = self._collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )

    # 3. Return the matched texts and their section labels
    return [
        {"section": results["metadatas"][0][i]["section"],
         "text": results["documents"][0][i]}
        for i in range(len(results["documents"][0]))
    ]
```

Concrete example — for the offer "Senior AI Engineer — Python, LLM, RAG systems":

```
→ [Technical skills]  "Python, FastAPI, LangGraph, scikit-learn"   (score: 0.92)
→ [Summary]           "I am a passionate Data Scientist..."          (score: 0.84)
→ [Experience]        "AI engineer at LG Electronics..."              (score: 0.79)
```

No keyword matching: "LangGraph" and "LLM systems" are semantically close even if the CV never says "LLM systems" explicitly.

---

### Step 5 — Augmented generation (LLM + context)

The retrieved CV sections and the job offer text are sent together to the LLM:

```python
# In utils/rag.py → analyze_offer() function
def analyze_offer(offer: dict, retrieved_chunks: list[dict]) -> str:
    # Format the retrieved CV context
    context = "\n\n".join(
        f"[{chunk['section']}] {chunk['text']}"
        for chunk in retrieved_chunks
    )

    messages = [
        {"role": "system", "content": """You are a recruitment expert. Analyse the match
         between the candidate profile and the job offer. Structure your answer in 3 parts:
         1. Strengths | 2. Gaps | 3. Suggestions"""},
        {"role": "user", "content":
            f"# Job offer\n{offer['description'][:2000]}\n\n"
            f"# Relevant CV sections\n{context}"},
    ]

    response = completion(model="ollama/qwen2.5:7b", messages=messages)
    return response.choices[0].message.content
```

The LLM receives targeted context (3 CV sections, not the whole CV), which:
- Reduces hallucination risk (it works from real facts extracted from the CV)
- Reduces context size (more efficient, fewer tokens)
- Improves precision (it analyses the right CV subset for this offer)

---

### Full pipeline diagram

```
CV (CVProfile)
    ↓ _chunk_profile()
[Summary] [Experience] [Skills] [Education] [Projects]
    ↓ model.encode()                    ↑
[0.23, -0.71, ...]                      │ retrieve()
    ↓ collection.add()                  │
    ChromaDB (chroma_db/)               │ query_embedding
    ↑___________________________________|
                              ↑
                       Job offer text
                       → model.encode()
                       → "Data Scientist Python RAG"
                       → [0.19, -0.68, ...]

Retrieved sections → LLM (Qwen 2.5) → Structured analysis
```

### Technical choices

- **`paraphrase-multilingual-MiniLM-L12-v2`**: HuggingFace embedding model, 471 MB, native French support, good quality/speed tradeoff on Apple M4 Pro
- **`ChromaDB PersistentClient`**: stores the index on disk (`./chroma_db/`), survives server restarts
- **`n_results=3`**: retrieve the 3 most relevant sections — enough context without overwhelming the LLM prompt
- **Section-based chunking** rather than fixed sliding-window chunking: better suited to CVs, which naturally have semantically homogeneous sections

---

## Phase 3 (continued) — Qualitative Evaluation with DeepEval

### Why unit tests are not enough for a RAG pipeline

Unit tests verify that the **code runs correctly**: the right number of chunks, the correct keys, no exceptions thrown. They say nothing about whether the pipeline produces **good answers**.

Two pipelines can have identical unit tests and yet produce very different quality:

```
Pipeline A: retrieves the wrong CV sections → generates a hallucinated analysis  ← unit tests PASS
Pipeline B: retrieves the right sections → generates a faithful, relevant analysis ← unit tests PASS
```

Qualitative evaluation adds a second layer: it measures the **semantic quality** of outputs, not just their structure.

---

### The three key RAG metrics

For a pipeline that retrieves CV sections and generates a job match analysis, three metrics matter:

| Metric | Question it answers | Applied to this project |
|---|---|---|
| **Contextual Relevancy** | Are the retrieved chunks relevant to the query? | Does `cv_rag.retrieve(offer_text)` return useful CV sections? |
| **Faithfulness** | Does the generated answer only use facts from the retrieved context? | Does `analyze_offer()` hallucinate skills absent from the CV? |
| **Answer Relevancy** | Does the answer directly address the question asked? | Does the analysis actually talk about the CV ↔ offer match? |

---

### DeepEval — a framework for LLM evaluation

DeepEval structures evaluation around a central object: the `LLMTestCase`.

```python
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

test_case = LLMTestCase(
    input="AI Engineer - Python / LangChain job offer...",       # the query
    actual_output="Here is the match analysis: ...",             # what the pipeline produced
    retrieval_context=["Developer at ACME. Built...", "Python, FastAPI..."],  # retrieved chunks
)

metric = FaithfulnessMetric(threshold=0.7, model=judge)
metric.measure(test_case)

print(metric.score)   # 0.0 to 1.0
print(metric.reason)  # the judge's explanation
```

- `input` → the query sent to the RAG pipeline (the job offer text)
- `actual_output` → what `analyze_offer()` returned
- `retrieval_context` → the chunks returned by `cv_rag.retrieve()`

DeepEval uses an LLM internally to *judge* each metric — this is the **LLM-as-a-judge** pattern (see below).

---

### LLM-as-a-judge

Traditional evaluation compares outputs to a fixed "expected answer" (ground truth). This is easy for classification tasks, but breaks down for free-text generation: there is no single correct answer to "is this analysis faithful to the CV?"

**LLM-as-a-judge** uses a second language model to evaluate the first:

```
your pipeline output
        ↓
   Judge LLM reads: output + retrieval_context + evaluation criteria
        ↓
   Score (0–1) + explanation
```

The judge LLM is given a specific rubric for each metric. For Faithfulness, it checks each claim in the output against the retrieved context and counts how many are actually supported.

**Limitation**: the judge model can itself make mistakes. A stronger judge (larger model, better instruction-following) produces more reliable scores. This is why judge quality matters independently of the pipeline being evaluated.

---

### Custom judge with `DeepEvalBaseLLM`

DeepEval defaults to OpenAI GPT-4 as its judge. To use a different model — Ollama, HuggingFace, Anthropic — you subclass `DeepEvalBaseLLM` and implement three methods:

```python
from deepeval.models import DeepEvalBaseLLM
import litellm

class OllamaJudge(DeepEvalBaseLLM):

    OLLAMA_MODEL = "ollama/qwen2.5:7b"

    def load_model(self) -> str:
        # Return the model identifier (or a model object for local models).
        return self.OLLAMA_MODEL

    def generate(self, prompt: str, schema=None) -> str | BaseModel:
        # DeepEval calls this with a prompt; we forward it to LiteLLM.
        # If schema is provided, DeepEval wants a structured Pydantic object back —
        # we handle this by embedding the schema in the prompt and parsing the JSON response.
        response = litellm.completion(
            model=self.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)   # synchronous fallback

    def get_model_name(self) -> str:
        return "qwen2.5:7b (Ollama local)"
```

The `schema` parameter is how DeepEval requests structured outputs from the judge. Since Ollama models don't support native function calling, we embed the JSON schema into the prompt and parse the response with `re.search(r"\{.*\}", raw, re.DOTALL)`.

---

### Why Ollama rather than HuggingFace for the judge

HuggingFace's **serverless inference API** (free tier) was initially the target for the judge model, but two blockers emerged:

1. **LiteLLM's `huggingface/` prefix** routes to HuggingFace's `/v1/chat/completions` endpoint, which only accepts a curated list of models — most models (including `Mistral-7B-Instruct-v0.3`) return `"not a chat model"`.
2. **HuggingFace Inference Providers** (the newer system) routes models through third-party providers (Cerebras, Sambanova, Novita…). Since mid-2024, this requires enabling providers in account settings *and* paying for most capable models — **there is no longer a meaningful free tier** for chat-capable models.

Ollama runs locally, costs nothing, and `qwen2.5:7b` is already used by this project for CV analysis — making it the natural judge choice.

**General lesson**: cloud inference APIs change pricing and availability faster than documentation updates. For reproducible local development, local inference (Ollama) is more stable than free-tier cloud endpoints.

---

### Separating quality tests from unit tests with pytest markers

Quality tests (DeepEval) make real LLM calls — they are slow (tens of seconds each) and depend on Ollama being running. Mixing them with unit tests would break the fast feedback loop.

**pytest markers** solve this by tagging tests so they can be run selectively:

```python
# In pyproject.toml — declare the custom marker:
[tool.pytest.ini_options]
markers = [
    "deepeval: quality tests using real LLMs — require Ollama running",
]

# In the test file — tag quality tests:
@pytest.mark.deepeval
def test_faithfulness(rag_result):
    ...
```

```bash
# Daily development — fast unit tests only:
pytest -m "not deepeval"

# When the RAG pipeline changes — run quality evaluation:
pytest -m deepeval -v -s
```

The `-s` flag (`--capture=no`) tells pytest not to suppress stdout, so `verbose_mode=True` on DeepEval metrics prints the judge's step-by-step reasoning directly in the terminal.

---

### Module-scoped fixtures for expensive setup

Quality tests share expensive setup (indexing the CV, generating an analysis with a real LLM call). Running this once per test function would triple the test duration.

`scope="module"` runs the fixture once for the entire test file:

```python
@pytest.fixture(scope="module")
def rag_result():
    """Index CV, retrieve chunks, generate analysis — once for the whole module."""
    cv_rag.index_cv(EVAL_PROFILE)
    query = f"{SAMPLE_OFFER['intitule']} {SAMPLE_OFFER['description']}"
    chunks = cv_rag.retrieve(query, n_results=3)
    analysis = analyze_offer(SAMPLE_OFFER, chunks)
    return {"query": query, "chunks": chunks, "analysis": analysis}
```

**Constraint**: module-scoped fixtures cannot depend on function-scoped fixtures (like `sample_profile` from `conftest.py`). The profile must be defined as a module-level constant in the quality test file — not a problem in practice since the evaluation profile is fixed by design.

---

### `verbose_mode=True` — reading the judge's reasoning

Adding `verbose_mode=True` to a metric makes DeepEval print its internal reasoning steps — which claims it checked, which it judged faithful or not, and why:

```python
metric = FaithfulnessMetric(threshold=0.7, model=OllamaJudge(), verbose_mode=True)
```

This is essential for debugging a failing quality test: instead of just seeing `score=0.4`, you see *which* claim in the output the judge flagged as unsupported by the retrieved context.

---

## Phase 4a — Cover Letter Multi-Agent Pipeline

### HITL (Human-in-the-loop) — multi-step chat confirmation

HITL is a design pattern where the system **pauses execution and asks the user to confirm or redirect** before continuing. The key idea is that some decisions should not be made autonomously by the agent — the user needs to be in control of them.

In this project, HITL controls the job search parameters through a chain of confirmation steps:

```
User types a role
    ↓
Bot asks: "Search for X?" → [✓ Yes] [✏️ Other]
    ↓ (if "Other")
LLM proposes 3 alternative roles + [✏️ Other...]
    ↓
Bot asks: "Which contract type?" → [CDI] [CDD] [Alternance] [Stage] [Any]
    ↓
Bot asks: "Experience level?" → [Beginner ≤1y] [Junior 1-3y] [Confirmed 3+y] [Any]
    ↓
Search is triggered with all 4 confirmed parameters
```

On the frontend, this is implemented as a **state machine** inside the chat component:

```jsx
const [chatState, setChatState] = useState("idle")
// possible values: "showSearchConfirm" | "showRolePicker" | "awaitingCustomRole"
//                  "showContratPicker" | "showExperiencePicker"
```

Each state renders a different set of quick-reply buttons. The user's click triggers the next state and eventually calls the search function with the confirmed parameters.

**Why not ask everything at once?** Progressive disclosure reduces cognitive load. Asking one question at a time is also closer to how a real recruiter conversation works — the user commits to each decision before seeing the next one.

---

### Multi-source RAG — indexing two knowledge bases in parallel

So far, the RAG pipeline only had one source: the CV. Phase 4a adds a second source: **GitHub repositories**, indexed separately from the CV.

```
cv_rag       → ChromaDB collection "cv_index"
github_rag   → ChromaDB collection "github_index"
```

Both use the same embedding model (`paraphrase-multilingual-MiniLM-L12-v2`), but they index different content:

```python
# cv_rag: chunks from the structured CVProfile (experiences, skills, summary…)
cv_rag.index_cv(cv_profile)

# github_rag: one chunk per GitHub repository (name + description + languages + topics)
github_rag.index_repos(list_of_repos)
```

At retrieval time, the two sources are queried **independently** with the same query text (the job offer). Each retrieval returns the chunks most relevant to the offer from its own domain:

```python
cv_matches      = cv_rag.retrieve(query)       # best-matching CV sections
github_matches  = github_rag.retrieve(query)   # best-matching GitHub repos
```

The two result sets are then passed separately to the LLM, which can draw on both sources without mixing them up.

**Why two separate collections and not one merged index?**
Keeping the sources separate allows the LLM to reason about them differently ("based on my experience…" vs "as shown by this project…"). It also makes it easy to add or update one source without rebuilding the other.

---

### LangGraph fan-out / fan-in — running nodes in parallel

**Fan-out** means a single node (or START) triggers **multiple nodes simultaneously** — they run in parallel.  
**Fan-in** means multiple parallel nodes all converge into a **single downstream node** that runs once both are done.

```
START
  ├──→ analyze_cv_matches     ─┐
  └──→ analyze_gh_matches     ─┴──→ assemble_cover_letter → END
```

The naïve implementation seems obvious — just add two edges:

```python
builder.add_edge(START, "analyze_cv_matches")
builder.add_edge(START, "analyze_gh_matches")
builder.add_edge("analyze_cv_matches", "assemble_cover_letter")
builder.add_edge("analyze_gh_matches", "assemble_cover_letter")
```

But this breaks in practice: LangGraph does **not** automatically wait for both parallel branches before triggering `assemble_cover_letter`. One branch completes, satisfies one edge, and the fan-in node fires — before the other branch has written its result to the state.

Symptom:
```python
result.keys()
# → ['offer', 'cv_matches', 'github_matches']   ← cover_letter is absent
# assemble_cover_letter never ran, or ran with an empty github_matches
```

---

### The fix — `Annotated` reducers + `Send` API

Two changes are needed, working together:

**1. `Annotated` reducers in the state**

`Annotated[list, operator.add]` tells LangGraph: "this channel supports concurrent writes — accumulate them instead of overwriting."

```python
from typing import Annotated, TypedDict
import operator

class CoverLetterState(TypedDict):
    offer: dict
    cv_matches: Annotated[list, operator.add]      # reducer: merge results from parallel branches
    github_matches: Annotated[list, operator.add]  # reducer: merge results from parallel branches
    cover_letter: str
```

Without this, LangGraph's default channel behaviour is "last write wins" (`LastValue`) — if two branches try to write around the same time, one update silently overwrites the other.

**2. Explicit fan-out with the `Send` API**

`Send` schedules a node explicitly with a copy of the current state, making the parallel dispatch unambiguous to LangGraph's scheduler:

```python
from langgraph.types import Send

def dispatch_rag_agents(state: CoverLetterState) -> list[Send]:
    return [
        Send("analyze_cv_matches", state),
        Send("analyze_gh_matches", state),
    ]

builder.add_conditional_edges(START, dispatch_rag_agents, ["analyze_cv_matches", "analyze_gh_matches"])
builder.add_edge("analyze_cv_matches", "assemble_cover_letter")
builder.add_edge("analyze_gh_matches", "assemble_cover_letter")
```

`add_conditional_edges` here is not used for a condition — the dispatcher always returns both `Send` objects. It is used because `Send` objects can only be returned from conditional edges, not plain `add_edge`.

**Why both changes are necessary together:**

| | `Annotated` reducers only | `Send` only | Both |
|---|---|---|---|
| Parallel nodes scheduled correctly | ✗ | ✓ | ✓ |
| State merged correctly before fan-in | ✓ | ✗ | ✓ |
| Fan-in node fires with complete state | ✗ | ✗ | ✓ |

The `Annotated` reducer defines *how* to merge state; the `Send` API defines *when* to schedule the nodes. Both are needed for a correct fan-in.

---

### `add_conditional_edges` for fan-out, not just routing

`add_conditional_edges` is usually taught as a tool for branching: "run this function, and depending on what it returns, go to node A or node B." But it has a second use: **returning a list of `Send` objects** to fan-out to multiple nodes at once.

```python
# Typical use — routing:
def route(state) -> str:
    return "node_a" if condition else "node_b"

builder.add_conditional_edges("some_node", route)

# Fan-out use — parallel dispatch:
def dispatch(state) -> list[Send]:
    return [Send("node_a", state), Send("node_b", state)]

builder.add_conditional_edges(START, dispatch, ["node_a", "node_b"])
```

The third argument (`["node_a", "node_b"]`) is the list of possible target nodes — LangGraph uses it to validate the graph at compile time.

---

## Phase 4b — Debugging embedding match quality

### Cosine similarity vs L2 distance — the metric must match the model's training objective

Two ways to compare two embedding vectors:

- **L2 (Euclidean) distance** — "how far apart are these two points?" Sensitive to both the *direction* of the vectors (the meaning) and their *length* (the norm) — a pure artefact, not signal.
- **Cosine similarity** — "what's the angle between these two vectors?" Ignores length entirely, keeps only direction.

`paraphrase-multilingual-MiniLM-L12-v2` (like most `sentence-transformers` models) is trained with a cosine-similarity objective. Using it and then comparing vectors with a distance function it wasn't optimized for (Chroma's default is L2) reintroduces noise unrelated to actual semantic closeness — a subtle bug that produces "roughly OK but not reliable" retrieval results, exactly the kind of thing that's hard to notice without measuring it directly.

**Fix — two changes that must be made together:**

```python
# 1. Normalize embeddings so only direction remains (length forced to 1)
embeddings = model.encode(texts, normalize_embeddings=True)

# 2. Tell Chroma to compare by angle (cosine), not raw L2 distance
collection = client.create_collection(name, metadata={"hnsw:space": "cosine"})
```

Doing only one of the two still leaves an inconsistent metric.

### `metadata={"hnsw:space": ...}` only applies at creation time

`get_or_create_collection(name, metadata=...)` silently **ignores** the `metadata` argument if the collection already exists — it only takes effect the first time the collection is created. This means changing the distance metric in code has **no effect on existing data** until the collection is deleted and rebuilt. Since `index_cv()` and `index_repos()` already do `delete_collection` + `create_collection` on every call, simply re-indexing the CV and the GitHub repos after the code change was enough to apply the fix — no manual DB reset needed.

### Diagnosing retrieval quality by asking Chroma for raw distances

`collection.query(...)` normally used through `retrieve()` only returns document text — the actual distance numbers behind a match are hidden. Passing `include=["distances", "metadatas", "documents"]` exposes them directly, which is the fastest way to *see* whether retrieval is behaving as expected instead of guessing from the final LLM output:

```python
results = collection.query(
    query_embeddings=query_embedding,
    n_results=collection.count(),
    include=["distances", "metadatas", "documents"],
)
for dist, meta, doc in zip(results["distances"][0], results["metadatas"][0], results["documents"][0]):
    similarity = 1 - dist   # with cosine space, distance = 1 - cosine_similarity
    print(f"[{meta['section']}] similarity={similarity:.4f}  {doc[:100]}")
```

A small standalone script (`backend/check_matching.py`, not part of the app) doing exactly this against a real, suspicious offer confirmed the fix worked: the CV's Algocat experience chunk (SDK Python, APIs REST, LLMs in production) scored ~0.71 cosine similarity against an "AI Software Engineer / FastAPI / Claude / RAG" offer — high because the tech vocabulary genuinely overlaps, not because of a bug.

### Embeddings capture semantic topic, not hard/structured constraints

An offer requiring "at least 4 years of Software Engineering experience" scored a high match even though that requirement wasn't clearly met. This is not a retrieval bug — **embeddings encode what a text is about, not verifiable facts about it**. Whether an offer says "4 years" or "10 years" barely moves the embedding, because "years of experience required" isn't the kind of information a semantic vector represents well.

This is exactly why the codebase already has a *separate*, non-embedding mechanism for skill matching (`tag_matched_skills`, `enrich_offer_detail` in `rag.py`) — extracting explicit facts and comparing them directly, rather than relying on similarity. The same pattern (extract a structured fact from the offer text, compare it deterministically to the candidate's data) would be needed for "years of experience required" — noted as a follow-up, not yet implemented.

**General lesson**: a RAG/embedding pipeline answers "is this semantically related?" — it does not answer "does this candidate qualify?" Hard, numeric, or categorical constraints need explicit extraction + rule-based comparison alongside the semantic score, not instead of it.

### Relative-to-batch percentage vs absolute score — a misleading UX pattern

The job search UI displayed a match percentage computed as:

```js
const maxScore = Math.max(...offers.map((o) => o.score ?? 0))
const ratio = offer.score / maxScore   // relative to the best offer in *this* batch
```

This means the top-ranked offer in *any* search always displays 100%, regardless of whether it's actually a strong match (0.9) or a mediocre one (0.5) — the percentage measures rank within the current results, not fit quality, but is presented visually as if it were absolute. This is what produced a "100% match" badge on an offer that didn't actually meet a stated requirement.

**Fix**: display `offer.score` directly (already bounded in a fixed, offer-independent range by the `1 / (1 + distance)` formula) instead of dividing by the batch's max. Trade-off: because that formula never reaches exactly 0% (a maximally dissimilar cosine distance of 2 still yields `1/(1+2) ≈ 33%`), percentages now sit in a narrower, lower band than before — a less flattering but more honest number.

## Phase 5 — BYOK: letting each user pick their own LLM model and API key

Goal: before deploying to production, let each user choose their LLM provider/model and supply their own API key ("Bring Your Own Key"), instead of the app always calling a hardcoded local Ollama model.

### Function parameters don't propagate automatically through a call chain

Adding `api_key: str | None = None` to `filter_technical_skills()` changes nothing about how `enrich_offer_detail()` behaves, because it called `filter_technical_skills(raw_competences)` — no `api_key` passed, so the default (`None`) is used regardless of what the outer caller received.

```python
def enrich_offer_detail(offer_detail, cv_skills, model=..., api_key=None):
    tech_competences = filter_technical_skills(raw_competences)  # api_key silently dropped here
```

**General lesson**: in Python, each function call is independent — there is no implicit mechanism for a parameter to "flow through" a call chain. A value has to be explicitly re-passed at *every* level between where it enters (the outermost caller) and where it's actually used (the innermost `completion()` call). Missing one link in the chain means that link silently falls back to its default — here, silently switching back to Ollama even though the user supplied a paid API key elsewhere.

### `litellm.completion(api_key=None)` is a safe no-op

Passing `api_key=None` explicitly to `litellm.completion()` behaves exactly as if `api_key` were never mentioned — litellm falls back to its normal resolution (environment variable, or nothing for a local Ollama model, which doesn't need a key at all). This is what makes the BYOK parameter backward-compatible: existing calls that don't supply a key keep working unchanged.

### `Annotated` reducers only matter for concurrent *writes*, not reads

Earlier (Phase 4a) we used `Annotated[list, operator.add]` so that two parallel LangGraph branches (dispatched via `Send`) wouldn't overwrite each other's output in the shared state. It's tempting to assume *any* field read by parallel branches needs the same treatment — but that's not the rule.

The reducer only matters for a state key that multiple concurrent branches **write to**. A key like `model`/`api_key`, set once before the fan-out and only **read** (never reassigned) by the parallel nodes, needs no reducer at all — a plain field in the `TypedDict` is enough, because there's no concurrent write to merge.

### Two very different kinds of "concurrency" in this app

"What happens when multiple users hit the app at the same time?" has two unrelated answers depending on where the state lives:

- **Per-request values** (function parameters, a LangGraph state field like `model`/`api_key`) are safe by construction: each HTTP request runs its own call stack with its own local variables, so two concurrent requests never see each other's `model`/`api_key`.
- **Module-level singletons** are not: `cv_rag = CVRagIndex()` and `github_rag = GitHubRepoIndex()` in `rag.py` are single instances shared by *every* request, pointing at a single, un-scoped ChromaDB collection name (`"cv_index"`). Likewise, `get_latest_cv()` in `database.py` does `ORDER BY id DESC LIMIT 1` with no `user_id` filter. Two users using the app at the same time can end up matched against each other's CV — a real bug, unrelated to the BYOK work, and a prerequisite to fix before a genuinely multi-user production deployment (would need per-user scoping: collection names, DB rows, etc.).

### MCP solves a different problem than BYOK

MCP (Model Context Protocol) standardizes how an LLM-driven **host** application (e.g. Claude Desktop, Claude Code) discovers and calls external **tools**/**resources**. It says nothing about which model the host itself uses, or which API key pays for that host's own completions — that's always decided by the host, outside MCP's scope.

BYOK is the opposite direction: *our own backend* is the one calling `completion()`, and we want *our own users* to supply the model/key for *that* call. MCP wouldn't replace anything here. It would become relevant in a different scenario: exposing this app's own capabilities (search offers, analyze a CV...) as MCP tools so an external host (e.g. Claude Code) could drive them — a possible future direction, not a solution to today's problem.

### FastAPI: headers + `Depends` for a cross-cutting concern that spans GET and POST

Some endpoints needing the LLM config are `GET` with just a query string (`/jobs/suggest-roles?role=...`), so there's no JSON body to add `model`/`api_key` fields to. HTTP headers work for both `GET` and `POST` alike, and a single shared FastAPI dependency avoids repeating "read these two headers" in every route:

```python
from dataclasses import dataclass
from fastapi import Header

@dataclass
class LLMConfig:
    model: str
    api_key: str | None

def get_llm_config(
    x_llm_model: str = Header(default="ollama/qwen2.5:7b"),
    x_llm_api_key: str | None = Header(default=None),
) -> LLMConfig:
    return LLMConfig(model=x_llm_model, api_key=x_llm_api_key)

@router.get("/suggest-roles")
def suggest_roles(role: str, llm: LLMConfig = Depends(get_llm_config)):
    ...
```

Detail worth remembering: FastAPI maps the parameter name `x_llm_model` to the HTTP header `X-Llm-Model` automatically — underscores become hyphens, matching standard HTTP header naming convention. The frontend has to send the hyphenated header name.

### Frontend: centralize a cross-cutting fetch concern the same way

The app had ~20 scattered `fetch('http://localhost:8000/...')` calls with no shared client. Rather than adding the two headers by hand at every call site (the same class of mistake as the `enrich_offer_detail` propagation gap above, just in JS), a small wrapper centralizes it once:

```js
// api.js
export function apiFetch(path, options = {}) {
  const { model, apiKey } = getLlmConfig()
  const headers = { ...options.headers, 'X-Llm-Model': model }
  if (apiKey) headers['X-Llm-Api-Key'] = apiKey
  return fetch(`${BASE_URL}${path}`, { ...options, headers })
}
```

Spreading `...options.headers` *before* adding the LLM headers means a caller's own headers (e.g. `Content-Type` for a JSON POST) are preserved, not overwritten.

### Testing "does the config propagate" is a plumbing test, not a quality test

This codebase already had two kinds of LLM-related tests: fast ones (`TestClient` + `unittest.mock.patch`, no network) and slow ones (`@pytest.mark.deepeval`, real Ollama calls judged for answer quality). Verifying that a header reaches the right function with the right value is neither — it's a **plumbing** test: does the value flow correctly through `Depends` → route → business function? Mocking the business function and asserting on its call arguments answers that in milliseconds, with no LLM involved:

```python
def test_suggest_roles_forwards_llm_config(sample_profile):
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.suggest_alternative_roles", return_value=["A", "B", "C"]) as mock_suggest:
        response = client.get(
            "/jobs/suggest-roles?role=Data Scientist",
            headers={"X-Llm-Model": "anthropic/claude-haiku-4-5", "X-Llm-Api-Key": "sk-test-123"},
        )
    mock_suggest.assert_called_once_with(
        sample_profile, searched_role="Data Scientist",
        model="anthropic/claude-haiku-4-5", api_key="sk-test-123",
    )
```

Pairing each "custom header" test with a "no header → falls back to the Ollama default" test caught the exact kind of silent-fallback bug described above, without needing a real model call either way.

### Still open after this phase

- The Settings UI itself (the frontend still always sends the Ollama default — nothing yet lets a user actually type in their own model/key).
- `/chat` (`main.py`) and `/cover/generate` (`cover.py`) also call an LLM but aren't wired to `get_llm_config` yet.
- The multi-user singleton/isolation issue above (`cv_rag`, `github_rag`, `get_latest_cv`) — a separate, more invasive piece of work.

**General lesson**: any time a displayed metric is computed relative to the current result set (`x / max(all x)`), consider whether the audience will read it as absolute. A relative ranking dressed up as a percentage is a classic way to accidentally overstate quality.
