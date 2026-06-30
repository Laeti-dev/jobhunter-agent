from graphs.state import CVState
from cv_model import CVProfile
from database import save_cv

def save_to_db_node(state: CVState) -> CVState:
    """Save the CV profile to the database."""
    cv_data = state["cv_data"]
    cv_profile = CVProfile.model_validate_json(cv_data)
    cv_id = save_cv(cv_profile)
    return {"cv_id": cv_id}
