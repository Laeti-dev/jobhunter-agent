import asyncio
import json

from dotenv import load_dotenv
load_dotenv()

import weave
from nodes.generate_cv_node import generate_cv_node


weave.init("jobhunter-agent")


dataset = [
    {
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
        "forbidden_soft_skills": ["travail en équipe", "team work"],
        "expected_tech_skills": ["python", "fastapi", "langgraph"],
    }
]


@weave.op()
def no_forbidden_soft_skills(output: str, forbidden_soft_skills: list[str]) -> dict:
    """Check that no explicitly refused soft skill appears in the generated CV."""
    cv_data = json.loads(output)
    soft_skills = [skill.lower() for skill in (cv_data.get("soft_skills") or [])]
    found = [forbidden for forbidden in forbidden_soft_skills if forbidden.lower() in soft_skills]
    return {"passed": len(found) == 0, "hallucinated_skills": found}


@weave.op()
def tech_skills_present(output: str, expected_tech_skills: list[str]) -> dict:
    """Check that the expected tech skills were correctly placed in tech_skills."""
    cv_data = json.loads(output)
    tech_skills = [skill.lower() for skill in (cv_data.get("tech_skills") or [])]
    missing = [skill for skill in expected_tech_skills if skill.lower() not in tech_skills]
    return {"passed": len(missing) == 0, "missing_skills": missing}


@weave.op()
def single_experience(output: str) -> dict:
    """Check that only one real experience was extracted (no phantom experience)."""
    cv_data = json.loads(output)
    experiences = cv_data.get("experiences") or []
    return {"passed": len(experiences) == 1, "experience_count": len(experiences)}


def make_model(model_name: str):
    @weave.op(name=f"generate_cv_with_{model_name}")
    def model(messages: list[dict]) -> str:
        state = {"messages": messages, "cv_data": None}
        result = generate_cv_node(state, model=model_name)
        return result["cv_data"]
    return model


async def main():
    scorers = [no_forbidden_soft_skills, tech_skills_present, single_experience]
    evaluation = weave.Evaluation(dataset=dataset, scorers=scorers)

    for model_name in ["ollama/llama3.2", "ollama/qwen2.5:7b"]:
        print(f"\n=== Evaluating {model_name} ===")
        await evaluation.evaluate(make_model(model_name))


if __name__ == "__main__":
    asyncio.run(main())
