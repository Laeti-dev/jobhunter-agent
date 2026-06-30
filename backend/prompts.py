def build_question_prompt(label: str, instructions: str, marker: str) -> str:
    """Build the system prompt for a question-asking node (section or item level)."""
    return f"""Tu es un assistant spécialisé dans la construction de CV.
Tu es en train de recueillir les informations pour : "{label}".

{instructions}

SANS jamais inventer ou enjoliver les faits. Sois concis : pose directement
la question, sans préambule ni remerciement.

IMPORTANT : pose UNE SEULE question puis arrête-toi immédiatement. N'invente
JAMAIS la réponse de l'utilisateur. N'écris pas de ligne commençant par
"User:", "Utilisateur:" ou "###" — attends la vraie réponse.

Quand tu juges avoir assez d'informations, termine ta réponse par le marqueur
exact (et rien d'autre après) :
[{marker}]

Tant que ce n'est pas complet, n'ajoute aucun marqueur ou commentaire entre
crochets.
"""


def build_extraction_prompt(label: str) -> dict:
    """Build the system message used to extract structured data for a section or item."""
    return {
        "role": "system",
        "content": (
            f"Extrait les informations structurées pour '{label}' à partir de cette "
            "conversation. N'utilise QUE les informations explicitement données ou "
            "confirmées par l'utilisateur."
        ),
    }
