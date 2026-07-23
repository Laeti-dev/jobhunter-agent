from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from cv_model import CVProfile

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_suggest_params_without_cv():
    with patch("routers.job_offers.get_latest_cv", return_value=None):
        response = client.get("/jobs/suggest-params")
    assert response.status_code == 404
    assert response.json()["detail"] == "Aucun CV trouvé."

def test_suggest_params_with_cv(sample_profile: CVProfile):
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile):
        response = client.get("/jobs/suggest-params")
    assert response.status_code == 200
    assert response.json() == {
        "keywords": sample_profile.target_role,
        "region": "11"
    }

def test_suggest_roles_forwards_llm_config(sample_profile: CVProfile):
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.suggest_alternative_roles", return_value=["A", "B", "C"]) as mock_suggest:
        response = client.get(
            "/jobs/suggest-roles?role=Data Scientist",
            headers={"X-Llm-Model": "anthropic/claude-haiku-4-5", "X-Llm-Api-Key": "sk-test-123"},
        )
    assert response.status_code == 200
    mock_suggest.assert_called_once_with(
        sample_profile,
        searched_role="Data Scientist",
        model="anthropic/claude-haiku-4-5",
        api_key="sk-test-123",
    )

def test_suggest_roles_defaults_without_headers(sample_profile: CVProfile):
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.suggest_alternative_roles", return_value=["A", "B", "C"]) as mock_suggest:
        response = client.get("/jobs/suggest-roles?role=Data Scientist")
    assert response.status_code == 200
    mock_suggest.assert_called_once_with(
        sample_profile,
        searched_role="Data Scientist",
        model="ollama/qwen2.5:7b",
        api_key=None,
    )

def test_enrich_forwards_llm_config(sample_profile: CVProfile):
    offer_detail = {"intitule": "Dev", "description": "desc", "competences": [], "contact": {}, "origineOffre": {}}
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.france_travail.get_offer", return_value=offer_detail), \
         patch("routers.job_offers.summarize_offer", return_value=["a", "b", "c"]) as mock_summarize, \
         patch("routers.job_offers.enrich_offer_detail", return_value={"matched_skills": [], "missing_skills": []}) as mock_enrich:
        response = client.get(
            "/jobs/123/enrich",
            headers={"X-Llm-Model": "anthropic/claude-haiku-4-5", "X-Llm-Api-Key": "sk-test-123"},
        )
    assert response.status_code == 200
    mock_summarize.assert_called_once_with("desc", model="anthropic/claude-haiku-4-5", api_key="sk-test-123")
    mock_enrich.assert_called_once_with(
        offer_detail, sample_profile.tech_skills,
        model="anthropic/claude-haiku-4-5", api_key="sk-test-123",
    )

def test_enrich_defaults_without_headers(sample_profile: CVProfile):
    offer_detail = {"intitule": "Dev", "description": "desc", "competences": [], "contact": {}, "origineOffre": {}}
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.france_travail.get_offer", return_value=offer_detail), \
         patch("routers.job_offers.summarize_offer", return_value=["a", "b", "c"]) as mock_summarize, \
         patch("routers.job_offers.enrich_offer_detail", return_value={"matched_skills": [], "missing_skills": []}) as mock_enrich:
        response = client.get("/jobs/123/enrich")
    assert response.status_code == 200
    mock_summarize.assert_called_once_with("desc", model="ollama/qwen2.5:7b", api_key=None)
    mock_enrich.assert_called_once_with(
        offer_detail, sample_profile.tech_skills,
        model="ollama/qwen2.5:7b", api_key=None,
    )

def test_analyze_forwards_llm_config(sample_profile: CVProfile):
    offer = {"intitule": "Dev", "description": "desc"}
    chunks = [{"section": "Résumé", "text": "Test summary."}]
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.france_travail.get_offer", return_value=offer), \
         patch("routers.job_offers.cv_rag.index_cv"), \
         patch("routers.job_offers.cv_rag.retrieve", return_value=chunks), \
         patch("routers.job_offers.analyze_offer", return_value="analysis text") as mock_analyze:
        response = client.post(
            "/jobs/analyze",
            json={"offer_id": "123"},
            headers={"X-Llm-Model": "anthropic/claude-haiku-4-5", "X-Llm-Api-Key": "sk-test-123"},
        )
    assert response.status_code == 200
    mock_analyze.assert_called_once_with(
        offer, chunks, model="anthropic/claude-haiku-4-5", api_key="sk-test-123",
    )

def test_analyze_defaults_without_headers(sample_profile: CVProfile):
    offer = {"intitule": "Dev", "description": "desc"}
    chunks = [{"section": "Résumé", "text": "Test summary."}]
    with patch("routers.job_offers.get_latest_cv", return_value=sample_profile), \
         patch("routers.job_offers.france_travail.get_offer", return_value=offer), \
         patch("routers.job_offers.cv_rag.index_cv"), \
         patch("routers.job_offers.cv_rag.retrieve", return_value=chunks), \
         patch("routers.job_offers.analyze_offer", return_value="analysis text") as mock_analyze:
        response = client.post("/jobs/analyze", json={"offer_id": "123"})
    assert response.status_code == 200
    mock_analyze.assert_called_once_with(
        offer, chunks, model="ollama/qwen2.5:7b", api_key=None,
    )
