"""
RAG quality tests using DeepEval.

These tests make real LLM calls (Ollama for generation, HuggingFace for judging)
and are therefore slower than unit tests. Run them separately with:

    pytest -m deepeval

Or skip them during normal development:

    pytest -m "not deepeval"
"""

import pytest
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

from cv_model import CVProfile, Experience, Education
from deepeval_judge import OllamaJudge
from utils.rag import cv_rag, analyze_offer


# A realistic job offer to evaluate the RAG pipeline against
SAMPLE_OFFER = {
    "intitule": "AI Engineer - Python / LangChain",
    "description": (
        "Nous recherchons un AI Engineer pour rejoindre notre équipe produit. "
        "Compétences requises : Python, FastAPI, LangChain ou LangGraph, "
        "expérience avec des LLMs (OpenAI, HuggingFace, modèles open-source). "
        "Vous travaillerez sur des pipelines RAG et des agents autonomes. "
        "Bac+5 ou équivalent en informatique ou data science requis."
    ),
}

# Profile defined here (not from conftest) because module-scoped fixtures
# cannot depend on function-scoped fixtures like sample_profile.
EVAL_PROFILE = CVProfile(
    name="Laeti Test",
    email="laeti@test.com",
    target_role="AI Engineer",
    summary="AI Engineer en reconversion, spécialisée en NLP et systèmes LLM.",
    experiences=[
        Experience(
            company="ACME",
            title="Developer",
            location="Paris",
            start_date="2023-01",
            achievements=["Developed a FastAPI service", "Built a LangGraph pipeline"],
            keywords=["Python", "FastAPI", "LangGraph"],
        )
    ],
    education=[
        Education(
            institution="Openclassrooms",
            degree="Master",
            field_of_study="AI Engineering",
            start_date="2024-01",
            achievements=[],
            keywords=[],
        )
    ],
    tech_skills=["Python", "FastAPI", "LangGraph", "HuggingFace"],
)


@pytest.fixture(scope="module")
def rag_result():
    """Index CV, retrieve chunks, generate analysis — once for the whole module."""
    cv_rag.index_cv(EVAL_PROFILE)
    query = f"{SAMPLE_OFFER['intitule']} {SAMPLE_OFFER['description']}"
    chunks = cv_rag.retrieve(query, n_results=3)
    analysis = analyze_offer(SAMPLE_OFFER, chunks)
    return {
        "query": query,
        "chunks": chunks,
        "analysis": analysis,
    }


@pytest.mark.deepeval
def test_retrieval_relevancy(rag_result):
    """Retrieved CV chunks should be relevant to the job offer query."""
    test_case = LLMTestCase(
        input=rag_result["query"],
        actual_output=rag_result["analysis"],
        retrieval_context=[c["text"] for c in rag_result["chunks"]],
    )
    metric = ContextualRelevancyMetric(threshold=0.5, model=OllamaJudge(), verbose_mode=True)
    metric.measure(test_case)

    assert metric.score >= 0.5, (
        f"Contextual relevancy too low: {metric.score:.2f}\nReason: {metric.reason}"
    )


@pytest.mark.deepeval
def test_faithfulness(rag_result):
    """The analysis must not invent facts absent from the retrieved CV chunks."""
    test_case = LLMTestCase(
        input=rag_result["query"],
        actual_output=rag_result["analysis"],
        retrieval_context=[c["text"] for c in rag_result["chunks"]],
    )
    metric = FaithfulnessMetric(threshold=0.7, model=OllamaJudge(), verbose_mode=True)
    metric.measure(test_case)

    assert metric.score >= 0.7, (
        f"Faithfulness too low: {metric.score:.2f}\nReason: {metric.reason}"
    )


@pytest.mark.deepeval
def test_answer_relevancy(rag_result):
    """The analysis must directly address the job offer, not be generic advice."""
    test_case = LLMTestCase(
        input=rag_result["query"],
        actual_output=rag_result["analysis"],
    )
    metric = AnswerRelevancyMetric(threshold=0.7, model=OllamaJudge(), verbose_mode=True)
    metric.measure(test_case)

    assert metric.score >= 0.7, (
        f"Answer relevancy too low: {metric.score:.2f}\nReason: {metric.reason}"
    )
