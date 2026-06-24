from litellm import completion
from graphs.state import CVState
from cv_model import CVProfile

def generate_cv_node(state: CVState, model: str = "ollama/qwen2.5:7b") -> CVState:
    messages = state["messages"] + [
        {"role": "system", "content": (
            "Génère le profil CV structuré à partir de cette conversation.\n\n"
            "RÈGLES STRICTES :\n"
            "- N'utilise QUE les informations explicitement données par l'utilisateur. "
            "N'invente aucune expérience, compétence ou réalisation absente de la conversation, "
            "même si elle te semble plausible ou déductible.\n"
            "- Pour `soft_skills` : n'inclus une compétence QUE SI l'utilisateur l'a confirmée "
            "explicitement après qu'elle lui a été proposée par l'agent (ex: l'agent demande "
            "« diriez-vous que... » et l'utilisateur répond positivement ou la reformule "
            "positivement). Si l'utilisateur n'a confirmé aucune soft skill, `soft_skills` "
            "doit être une liste vide — ne complète JAMAIS avec des soft skills déduites "
            "par toi-même à cette étape."
        )}
    ]
    response = completion(
        model=model,
        messages=messages,
        response_format=CVProfile,
        temperature=0.1,
    )
    cv_json = response.choices[0].message.content
    return {"messages": state["messages"], "cv_data": cv_json}
