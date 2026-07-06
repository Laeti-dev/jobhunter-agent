import pytest
from unittest.mock import patch
import numpy as np

from cv_model import CVProfile
from utils.rag import cv_rag


def test_cv_has_been_chunked_correctly(sample_profile: CVProfile) -> list[dict]:
    chunks = cv_rag._chunk_profile(sample_profile)
    assert len(chunks) == 5
    assert len([c for c in chunks if c["section"] == "Résumé"]) == 1
    assert len([c for c in chunks if c["section"] == "Poste visé"]) == 1
    assert len([c for c in chunks if c["section"] == "Expérience"]) == 1
    assert len([c for c in chunks if c["section"] == "Formation"]) == 1
    assert len([c for c in chunks if c["section"] == "Compétences techniques"]) == 1
    assert len([c for c in chunks if c["section"] == "Projet"]) == 0
    assert len([c for c in chunks if c["section"] == "Soft skills"]) == 0
    for c in chunks:
        assert "id" in c
        assert "section" in c
        assert "text" in c

def test_retrieve_returns_closest_chunks(sample_profile: CVProfile):
    def mock_encode(texts):
        """Return a fixed-dimension vector for each text."""
        return np.array([[1.0] * 10 for _ in texts])

    with patch.object(cv_rag, "model") as mock_model:
        mock_model.encode.side_effect = mock_encode
        cv_rag.index_cv(sample_profile)
        results = cv_rag.retrieve("AI Engineer", n_results=3)

    assert len(results) == 3
    for r in results:
        assert "section" in r
        assert "text" in r
    sections = {r["section"] for r in results}
    assert "Résumé" in sections
