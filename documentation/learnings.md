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
