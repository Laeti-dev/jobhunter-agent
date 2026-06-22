from nodes.generate_cv_node import generate_cv_node

fake_conversation = {
    "messages": [
        {"role": "user", "content": "Je m'appelle Laetitia, mon email est laetitia@example.com"},
        {"role": "assistant", "content": "Merci, quel poste visez-vous ?"},
        {"role": "user", "content": "Je vise un poste d'AI Engineer junior."},
        {"role": "assistant", "content": "Parlez-moi de votre expérience professionnelle."},
        {"role": "user", "content": "J'ai travaillé 5 ans en restauration comme cheffe de rang, "
                                     "avant de me reconvertir vers l'IA en 2024."},
        {"role": "assistant", "content": "Quelles sont vos compétences techniques ?"},
        {"role": "user", "content": "Python, FastAPI, LangGraph, et des bases en machine learning."},
        {"role": "assistant", "content": "Diriez-vous que votre expérience en restauration vous a "
                                          "permis de développer la gestion du stress et le travail "
                                          "en équipe ?"},
        {"role": "user", "content": "Oui pour la gestion du stress, par contre je travaillais plutôt "
                                     "seule en salle, donc pas vraiment le travail en équipe."},
    ],
    "cv_data": None,
}

result = generate_cv_node(fake_conversation)
print(result["cv_data"])
