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
from nodes.generate_cv_node import generate_cv_node
fake_state = {"messages": [...], "cv_data": None}
result = generate_cv_node(fake_state)
print(result["cv_data"])
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
