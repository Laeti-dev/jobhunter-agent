import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graphs.state import CVState
from sections import SECTIONS
from nodes.ask_in_section_node import ask_in_section_node
from nodes.extract_section_node import extract_section_node
from nodes.ask_in_item_node import ask_in_item_node
from nodes.extract_item_node import extract_item_node
from nodes.ask_continue_node import ask_continue_node
from nodes.handle_continue_answer_node import handle_continue_answer_node
from nodes.assemble_cv_node import assemble_cv_node
from nodes.save_to_db_node import save_to_db_node


def route_entry(state: CVState) -> str:
    """Decide which node should handle the incoming message."""
    if state["awaiting_continue"]:
        return "handle_continue_answer"
    section = SECTIONS[state["section_index"]]
    return "ask_in_item" if section["is_list"] else "ask_in_section"


def _user_message_count(state: CVState) -> int:
    return sum(1 for m in state["context_messages"] if m["role"] == "user")


def route_after_section_question(state: CVState) -> str:
    section = SECTIONS[state["section_index"]]
    last_message = state["context_messages"][-1]["content"]
    min_messages = section.get("min_user_messages", 2)
    if "[SECTION_DONE]" in last_message and _user_message_count(state) >= min_messages:
        return "extract_section"
    return END


def route_after_item_question(state: CVState) -> str:
    section = SECTIONS[state["section_index"]]
    last_message = state["context_messages"][-1]["content"]
    min_messages = section.get("min_user_messages", 2)
    if "[ITEM_DONE]" in last_message and _user_message_count(state) >= min_messages:
        return "extract_item"
    return END


def route_after_section_advance(state: CVState) -> str:
    """After a flat section (or a finished list section) is done, decide what's next."""
    if state["section_index"] >= len(SECTIONS):
        return "assemble_cv"
    next_section = SECTIONS[state["section_index"]]
    return "ask_in_item" if next_section["is_list"] else "ask_in_section"


def route_after_continue(state: CVState) -> str:
    if state["wants_more_items"]:
        return "ask_in_item"
    return route_after_section_advance(state)


builder = StateGraph(CVState)
builder.add_node("ask_in_section", ask_in_section_node)
builder.add_node("extract_section", extract_section_node)
builder.add_node("ask_in_item", ask_in_item_node)
builder.add_node("extract_item", extract_item_node)
builder.add_node("ask_continue", ask_continue_node)
builder.add_node("handle_continue_answer", handle_continue_answer_node)
builder.add_node("assemble_cv", assemble_cv_node)
builder.add_node("save_to_db", save_to_db_node)

builder.add_conditional_edges(START, route_entry)
builder.add_conditional_edges("ask_in_section", route_after_section_question)
builder.add_conditional_edges("extract_section", route_after_section_advance)
builder.add_conditional_edges("ask_in_item", route_after_item_question)
builder.add_edge("extract_item", "ask_continue")
builder.add_edge("ask_continue", END)
builder.add_conditional_edges("handle_continue_answer", route_after_continue)
builder.add_edge("assemble_cv", "save_to_db")
builder.add_edge("save_to_db", END)

_conn = sqlite3.connect("cv_sessions.db", check_same_thread=False)
checkpointer = SqliteSaver(_conn)
cv_graph = builder.compile(checkpointer=checkpointer)
