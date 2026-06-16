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

### Tooling lessons

- Poetry and Homebrew can install multiple Python versions — always set the correct one with `poetry env use /path/to/python3.12`
- Node.js version matters: Vite 6 requires Node 20.19+ or 22+ — use **nvm** to manage Node versions cleanly
- `nvm install 22 && nvm use 22` upgrades Node without breaking other projects
- When npm optional dependencies fail to install (rolldown binding issue), delete `node_modules` and `package-lock.json` then reinstall
