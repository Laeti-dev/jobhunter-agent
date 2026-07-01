import time
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
API_BASE = "https://api.francetravail.io/partenaire/offresdemploi/v2"
SCOPE = "api_offresdemploiv2 o2dsoffre"

DEFAULT_REGION = "11"  # Île-de-France


class FranceTravailClient:
    """Client for the France Travail (Pôle Emploi) job offers API."""

    def __init__(self):
        self._client_id = os.getenv("CLIENT_ID")
        self._client_secret = os.getenv("CLIENT_SECRET")
        self._token: str | None = None
        self._expires_at: float = 0

    def _get_token(self) -> str:
        """Return a valid OAuth2 token, refreshing it if necessary."""
        if self._token and time.time() < self._expires_at - 60:
            return self._token

        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
        }

    def get_regions(self) -> list[dict]:
        """Return all regions from France Travail's referentiel."""
        response = httpx.get(
            f"{API_BASE}/referentiel/regions",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def find_region(self, region_name: str) -> dict | None:
        """Find the best matching region by name (exact match first, then partial)."""
        results = self.get_regions()
        if not results:
            return None
        search = region_name.upper().strip()
        for region in results:
            if region.get("libelle", "").upper() == search:
                return region
        for region in results:
            if search in region.get("libelle", "").upper():
                return region
        return None

    def search_offers(
        self,
        mots_cles: str,
        region: str = DEFAULT_REGION,
        experience: str | None = None,
        niveau_formation: str | None = None,
        max_results: int = 10,
    ) -> list[dict]:
        """Search for job offers in a region (INSEE 2-digit code, default: Île-de-France)."""
        params: dict = {
            "motsCles": mots_cles,
            "region": region,
            "range": f"0-{max_results - 1}",
        }
        if experience:
            params["experience"] = experience
        if niveau_formation:
            params["niveauFormation"] = niveau_formation

        response = httpx.get(
            f"{API_BASE}/offres/search",
            params=params,
            headers=self._headers(),
        )
        response.raise_for_status()
        if not response.content:
            return []
        data = response.json()
        return data.get("resultats", [])

    def get_education_levels(self) -> list[dict]:
        """Return all education levels from France Travail's referentiel."""
        response = httpx.get(
            f"{API_BASE}/referentiel/niveauxFormations",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def get_offer(self, offer_id: str) -> dict:
        """Return the details of a specific job offer."""
        response = httpx.get(
            f"{API_BASE}/offres/{offer_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()


france_travail = FranceTravailClient()
