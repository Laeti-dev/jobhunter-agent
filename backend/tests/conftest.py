import pytest
from cv_model import CVProfile, Experience, Education


@pytest.fixture
def sample_profile() -> CVProfile:
    """A minimal valid CVProfile shared across all test files."""
    return CVProfile(
        name="Laeti Test",
        email="laeti@test.com",
        target_role="AI Engineer",
        summary="Test summary.",
        experiences=[
            Experience(
                company="ACME",
                title="Developer",
                location="Paris",
                start_date="2023-01",
                achievements=["Built things"],
                keywords=[],
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
        tech_skills=["Python", "FastAPI"],
    )
