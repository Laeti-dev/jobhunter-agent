from langgraph.graph import StateGraph, START, END
from litellm import completion
from graphs.state import CVState
from nodes.generate_cv_node import generate_cv_node
from nodes.save_to_db_node import save_to_db_node


SYSTEM_PROMPT = """Tu es un assistant spécialisé dans la construction de CV.
Ton rôle est de poser des questions pertinentes, une à la fois, pour collecter
les informations nécessaires à un CV solide — SANS jamais inventer ou enjoliver
les faits. Si une réponse est vague, demande des précisions concrètes (chiffres,
résultats mesurables, exemples).

Tu dois couvrir ces sections, dans cet ordre :
1. Identité : nom, email, téléphone, ville, poste visé
2. Expériences professionnelles : poste, entreprise, dates, missions principales,
   réalisations concrètes (avec chiffres si possible)
3. Formation : diplôme, établissement, année
4. Compétences techniques
5. Langues parlées et niveau réel
6. Projets personnels ou professionnels notables

Après avoir recueilli une expérience professionnelle, tu peux déduire des soft
skills probables à partir de cette expérience (ex: gestion du stress pour un
poste en restauration). Dans ce cas, propose-les explicitement à l'utilisateur
sous forme de question ("Diriez-vous que vous avez développé X et Y dans ce
poste ?") et ne les retiens QUE si l'utilisateur les confirme ou les corrige.
Ne les affirme jamais sans validation explicite de l'utilisateur.

Pose une seule question à la fois. Quand tu juges avoir assez d'informations
pour générer un CV complet et honnête, termine ta réponse par le marqueur exact :
[CV_READY]
"""


def agent_node(state: CVState) -> CVState:
    """Ask the next relevant question based on the conversation so far."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = completion(
        model="ollama/llama3.2",
        messages=messages,
    )
    assistant_message = {
        "role": "assistant",
        "content": response.choices[0].message.content,
    }
    return {"messages": state["messages"] + [assistant_message]}

def route_to_generate_cv(state: CVState) -> str:
    """Decide whether to generate the CV now or wait for the next user message."""
    last_message = state["messages"][-1]["content"]
    return "generate_cv" if "[CV_READY]" in last_message else END

builder = StateGraph(CVState)
builder.add_node("agent", agent_node)
builder.add_node("generate_cv", generate_cv_node)
builder.add_node("save_to_db", save_to_db_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_to_generate_cv)
builder.add_edge("generate_cv", "save_to_db")
builder.add_edge("save_to_db", END)

cv_graph = builder.compile()
