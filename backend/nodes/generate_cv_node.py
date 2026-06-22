from litellm import completion
from graphs.state import CVState
from cv_model import CVProfile

def generate_cv_node(state: CVState, model: str = "ollama/llama3.2") -> CVState:
    messages = state["messages"] + [
        {"role": "system", "content": (
            "Génère le profil CV structuré à partir de cette conversation. "
            "N'utilise QUE les informations explicitement données ou confirmées "
            "par l'utilisateur — n'invente aucune compétence, expérience ou "
            "réalisation qui n'a pas été mentionnée ou validée dans l'échange."
        )}
    ]
    response = completion(
        model=model,
        messages=messages,
        response_format=CVProfile,
    )
    cv_json = response.choices[0].message.content
    return {"messages": state["messages"], "cv_data": cv_json}
