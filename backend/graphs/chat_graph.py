from langgraph.graph import StateGraph, START, END
from litellm import completion
from graphs.state import BaseState as State

def chat_node(state: State) -> State:
    """Call the LLM with the current conversation history."""
    response = completion(
        model="ollama/llama3.2",
        messages=state["messages"],
    )
    assistant_message = {
        "role": "assistant",
        "content": response.choices[0].message.content,
    }
    return {"messages": state["messages"] + [assistant_message]}

builder = StateGraph(State)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

graph = builder.compile()
