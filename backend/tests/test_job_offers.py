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
