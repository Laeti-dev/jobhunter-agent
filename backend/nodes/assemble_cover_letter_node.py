from graphs.state import CoverLetterState
from litellm import completion

def assemble_cover_letter_node(state: CoverLetterState) -> dict:
    # Retrieve elements
    offer = state["offer"]
    cv_matches = state["cv_matches"]
    github_matches = state["github_matches"]

    # Format matches
    cv_matches_text = "\n".join([f"- {match['text']}" for match in cv_matches])
    github_matches_text = "\n".join([f"- {match['repo']} {match['text'][:500]}" for match in github_matches])

    messages = [
        {
            "role": "system",
            "content": f"""
            Tu es un expert en rédaction de lettres de motivation.
            Tu es chargé de rédiger une lettre professionnelle en {offer.get('language', 'français')}
            à la première personne.
            Appuie toi UNIQUEMENT sur les éléments fournis, sans rien inventer.
            Mets en avant les expériences et projets les plus pertinents pour le poste.
            """
        },
        {
            "role": "user",
            "content": f"""
            Poste visé : {offer.get('intitule', '')}
            Sommaire de l'offre : {offer.get('summary', [])}
            # Expérience pertinentes trouvées dans le CV:
            {cv_matches_text}
            # Projets GitHub pertinents :
            {github_matches_text}

            Rédige la lettre de motivation en {offer.get('language', 'français')}
            """
        }
    ]
    response = completion(
        model="ollama/qwen2.5:7b",
        messages=messages,
        temperature=0.7
    )
    cover_letter_text = response.choices[0].message.content
    return {"cover_letter": cover_letter_text}
