import pytest
from cv_model import CVProfile, Experience, Education
from utils.database import init_db, save_cv, get_latest_cv


@pytest.fixture
def db(monkeypatch, tmp_path):
    """Redirect database writes to a temporary file for each test."""
    monkeypatch.setattr("utils.database.DB_PATH", str(tmp_path / "test.db"))
    init_db()


@pytest.fixture
def sample_profile() -> CVProfile:
    """A minimal valid CVProfile for use in tests."""
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


def test_get_latest_cv_returns_none_on_empty_db(db):
    result = get_latest_cv()
    assert result is None


def test_save_cv_returns_positive_id(db, sample_profile):
    cv_id = save_cv(sample_profile)
    assert isinstance(cv_id, int)
    assert cv_id > 0


def test_save_and_retrieve_cv(db, sample_profile):
    save_cv(sample_profile)
    retrieved = get_latest_cv()

    assert retrieved is not None
    assert retrieved.name == sample_profile.name
    assert retrieved.email == sample_profile.email
    assert retrieved.target_role == sample_profile.target_role
    assert retrieved.tech_skills == sample_profile.tech_skills


def test_get_latest_cv_returns_most_recent(db, sample_profile):
    save_cv(sample_profile)

    newer_profile = sample_profile.model_copy(update={"name": "Updated Name"})
    save_cv(newer_profile)

    retrieved = get_latest_cv()
    assert retrieved.name == "Updated Name"
