from graphs.cv_graph import cv_graph

conversation = {
    "messages": [
        {"role": "user", "content": "Bonjour, je veux construire mon CV. Je m'appelle Laetitia Ikusawa, mon email est laetitia.ikusawa@gmail.com, je vise un poste d'AI Engineer junior."},
        {"role": "assistant", "content": "Pouvez-vous me dire dans quelle ville tu habites actuellement ?"},
        {"role": "user", "content": "J'habite à Paris. J'ai travaillé 5 ans en restauration comme cheffe de rang, avant de me reconvertir vers l'IA en 2024."},
        {"role": "assistant", "content": "Pouvez-vous me donner les détails de ta formation professionnelle ?"},
        {"role": "user", "content": "Je suis en master AI Engineer, actuellement en formation, en reconversion depuis la restauration."},
        {"role": "assistant", "content": "Quels sont les principaux thèmes abordés dans ton master AI Engineer ? As-tu effectué un stage ?"},
        {"role": "user", "content": "Mon master couvre le Machine Learning, le NLP et les LLMs. Pas de stage encore. Mes compétences techniques : Python, FastAPI, LangGraph, LiteLLM, scikit-learn. Je parle français (langue maternelle) et anglais (courant). Comme projet, j'ai construit cet agent de recherche d'emploi avec un chatbot et un CV builder basés sur LangGraph et Ollama."},
        {"role": "assistant", "content": "Pouvez-vous me donner plus de détails sur ton expérience professionnelle dans la restauration, comme le poste que tu as occupé, l'entreprise dans laquelle tu travaillais et les missions principales que tu as accomplies ?"},
        {"role": "user", "content": "J'étais cheffe de rang chez Le Bistrot Parisien de 2019 à 2024. Mes missions : accueil et service de 40 couverts par soir, gestion des commandes, formation des nouveaux serveurs, gestion des conflits clients. Cela m'a appris la gestion du stress sous forte charge. Je pense avoir donné toutes les informations nécessaires pour mon CV, tu peux le générer maintenant."},
        {"role": "assistant", "content": "Pouvez-vous me donner plus de détails sur ton projet d'agent de recherche d'emploi ? As-tu déjà collaboré avec d'autres équipes ?"},
        {"role": "user", "content": "Le projet est personnel, solo, pas de travail en équipe pour l'instant. L'objectif est d'apprendre l'agentic AI et le RAG en construisant un outil utile pour ma propre recherche d'emploi. J'ai terminé de répondre à toutes tes questions, merci de générer le CV maintenant, je n'ai rien à ajouter."},
    ],
    "cv_data": None,
    "cv_id": None,
}

result = cv_graph.invoke(conversation)

print("--- Dernier message de l'agent ---")
print(result["messages"][-1]["content"])
print("\n--- cv_data ---")
print(result.get("cv_data"))
print("\n--- cv_id ---")
print(result.get("cv_id"))
