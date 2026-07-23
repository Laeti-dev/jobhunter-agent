from sentence_transformers import SentenceTransformer
import chromadb
import json
from litellm import completion
from cv_model import CVProfile
from utils.database import get_latest_cv

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # multilingual for French support
COLLECTION_NAME = "cv_index"
GITHUB_COLLECTION_NAME = "github_projects"

# Single model instance shared by all RAG classes — loading once saves ~2s at startup
_embedding_model = SentenceTransformer(MODEL_NAME)


class CVRagIndex:
    def __init__(self):
        self.model = _embedding_model
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self._collection = None

    def _chunk_profile(self, profile: CVProfile) -> list[dict]:
        """Split a CVProfile into text chunks, one per meaningful section."""
        chunks = []

        if profile.summary:
            chunks.append({"id": "summary", "section": "Résumé", "text": profile.summary})

        if profile.target_role:
            chunks.append({"id": "target_role", "section": "Poste visé",
                           "text": f"Poste visé : {profile.target_role}"})

        for i, exp in enumerate(profile.experiences or []):
            text = f"{exp.title} chez {exp.company}. " + ". ".join(exp.achievements or [])
            chunks.append({"id": f"exp_{i}", "section": "Expérience", "text": text})

        for i, edu in enumerate(profile.education or []):
            text = f"{edu.degree} en {edu.field_of_study} à {edu.institution}"
            chunks.append({"id": f"edu_{i}", "section": "Formation", "text": text})

        if profile.tech_skills:
            chunks.append({"id": "tech_skills", "section": "Compétences techniques",
                           "text": "Compétences techniques : " + ", ".join(profile.tech_skills)})

        if profile.soft_skills:
            chunks.append({"id": "soft_skills", "section": "Soft skills",
                           "text": "Soft skills : " + ", ".join(profile.soft_skills)})

        for i, project in enumerate(profile.projects or []):
            text = f"Projet : {project.title}. {project.description}. Technologies : {', '.join(project.technologies or [])}"
            chunks.append({"id": f"proj_{i}", "section": "Projet", "text": text})

        return chunks

    def index_cv(self, profile: CVProfile) -> None:
        """Embed all CV sections and store them in ChromaDB."""
        chunks = self._chunk_profile(profile)

        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        # hnsw:space="cosine" tells Chroma to compare vectors by angle, not raw distance —
        # this must match normalize_embeddings=True below, otherwise the metric is inconsistent
        self._collection = self.client.create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [{"section": c["section"]} for c in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def retrieve(self, query_text: str, n_results: int = 3) -> list[dict]:
        """Find the most semantically similar CV sections for a given job offer text."""
        if self._collection is None:
            raise RuntimeError("CV not indexed yet — call index_cv first.")

        query_embedding = self.model.encode([query_text], normalize_embeddings=True).tolist()
        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
        )
        return [
            {
                "section": results["metadatas"][0][i]["section"],
                "text": results["documents"][0][i],
            }
            for i in range(len(results["documents"][0]))
        ]


class GitHubRepoIndex:
    """Index GitHub repo documents in ChromaDB for multi-source RAG."""

    def __init__(self):
        self.model = _embedding_model
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self._collection = None

    def index_repos(self, documents: list[str], repo_names: list[str]) -> None:
        """Embed repo documents and store them in ChromaDB."""
        try:
            self.client.delete_collection(GITHUB_COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self.client.create_collection(GITHUB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

        embeddings = self.model.encode(documents, normalize_embeddings=True).tolist()
        self._collection.add(
            ids=repo_names,
            embeddings=embeddings,
            documents=documents,
            metadatas=[{"repo": name} for name in repo_names],
        )

    def retrieve(self, query_text: str, n_results: int = 3) -> list[dict]:
        """Find the most relevant GitHub repos for a given job offer query."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(GITHUB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

        count = self._collection.count()
        if count == 0:
            return []

        query_embedding = self.model.encode([query_text], normalize_embeddings=True).tolist()
        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_results, count),
        )
        return [
            {
                "repo": results["metadatas"][0][i]["repo"],
                "text": results["documents"][0][i],
            }
            for i in range(len(results["documents"][0]))
        ]

    def list_repos(self) -> list[str]:
        """Return the names of all indexed repos."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(GITHUB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        results = self._collection.get()
        return [meta["repo"] for meta in results["metadatas"]]


cv_rag = CVRagIndex()
github_rag = GitHubRepoIndex()


def analyze_offer(
    offer: dict,
    retrieved_chunks: list[dict],
    model: str = "ollama/qwen2.5:7b",
    api_key: str | None = None,
) -> str:
    """Generate a RAG-powered match analysis between a job offer and the retrieved CV sections."""
    context = "\n\n".join(
        f"[{chunk['section']}] {chunk['text']}" for chunk in retrieved_chunks
    )
    offer_text = f"{offer.get('intitule', '')}\n\n{offer.get('description', '')[:2000]}"

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un expert en recrutement. Analyse la correspondance entre le profil "
                "candidat et l'offre d'emploi fournie. Structure ta réponse en 3 parties :\n"
                "1. **Points forts** : Ce qui correspond bien entre le profil et l'offre\n"
                "2. **Lacunes** : Ce qui manque ou semble insuffisant\n"
                "3. **Suggestions** : Comment préparer sa candidature\n\n"
                "Sois concis, honnête et constructif. Base-toi UNIQUEMENT sur les "
                "informations fournies, sans inventer."
            ),
        },
        {
            "role": "user",
            "content": (
                f"# Offre d'emploi\n{offer_text}\n\n"
                f"# Sections pertinentes du CV\n{context}"
            ),
        },
    ]

    response = completion(model=model, messages=messages, temperature=0.3, api_key=api_key)
    return response.choices[0].message.content


def suggest_alternative_roles(
    cv: CVProfile,
    searched_role: str,
    model: str = "ollama/qwen2.5:7b",
    api_key: str | None = None,
) -> list[str]:
    """Ask the LLM to suggest 3 job titles close to searched_role, based on the CV profile."""
    skills = ", ".join((cv.tech_skills or [])[:10]) or "non précisées"

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un conseiller en orientation professionnelle. "
                "Réponds UNIQUEMENT avec un tableau JSON de 3 chaînes de caractères, "
                "sans texte supplémentaire ni markdown. "
                "Exemple : [\"Titre A\", \"Titre B\", \"Titre C\"]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Un candidat cherche un poste de **{searched_role}**.\n"
                f"Ses compétences : {skills}\n\n"
                "Propose 3 titres de postes proches ou similaires, "
                "que l'on trouve couramment sur le marché de l'emploi français."
            ),
        },
    ]

    response = completion(model=model, messages=messages, temperature=0.7, api_key=api_key)
    content = response.choices[0].message.content.strip()
    roles = json.loads(content)
    if not isinstance(roles, list):
        raise ValueError("Le LLM n'a pas renvoyé un tableau JSON.")
    return [str(r) for r in roles[:3]]


def filter_technical_skills(
    skills: list[str],
    model: str = "ollama/qwen2.5:7b",
    api_key: str | None = None,
) -> list[str]:
    """
    Send a list of raw competences to the LLM.
    Returns only the technical ones (languages, frameworks, tools, methodologies).
    One single LLM call — designed to be used on a batch across all offers.
    """
    if not skills:
        return []

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un expert en recrutement tech. "
                "Réponds UNIQUEMENT avec un tableau JSON des compétences techniques, "
                "sans texte supplémentaire ni markdown. "
                "Garde : langages, frameworks, outils, technologies, méthodes techniques (ex: Agile, CI/CD). "
                "Exclus : soft skills, qualités personnelles, compétences non techniques "
                "(ex: 'Travail en équipe', 'Rigueur', 'Sens du service'). "
                "Exemple de sortie : [\"Python\", \"Docker\", \"SQL\", \"Agile\"]"
            ),
        },
        {
            "role": "user",
            "content": f"Filtre cette liste : {json.dumps(skills, ensure_ascii=False)}",
        },
    ]

    response = completion(model=model, messages=messages, temperature=0.1, api_key=api_key)
    content = response.choices[0].message.content.strip()
    try:
        filtered = json.loads(content)
        if isinstance(filtered, list):
            return [str(s) for s in filtered]
    except json.JSONDecodeError:
        pass
    return skills  # fallback: keep all if parsing fails


def tag_matched_skills(offer: dict, cv_skills_lower: list[str]) -> list[str]:
    """
    Return CV skills (lowercase) found by substring in the offer text.
    Used at search time — only green tags, no missing skills yet.
    """
    offer_text = f"{offer.get('intitule', '')} {offer.get('description', '')}".lower()
    return [s for s in cv_skills_lower if s in offer_text][:6]


def summarize_offer(description: str, model: str = "ollama/qwen2.5:7b", api_key: str | None = None) -> list[str]:
    """Ask the LLM to summarize an offer description in exactly 3 bullet points."""
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un expert en recrutement. Résume l'offre en exactement 3 points clés : "
                "les missions principales séparées par des points-virgules, la stack technique, et le profil attendu. "
                "Réponds UNIQUEMENT avec un tableau JSON de 3 chaînes, sans texte ni markdown. "
                "Exemple : [\"Mission A ; Mission B ; Mission C\", \"Stack demandée\", \"Profil recherché\"]"
            ),
        },
        {
            "role": "user",
            "content": f"Résume cette offre en 3 points :\n\n{description[:3000]}",
        },
    ]
    response = completion(model=model, messages=messages, temperature=0.3, api_key=api_key)
    content = response.choices[0].message.content.strip()
    try:
        bullets = json.loads(content)
        if isinstance(bullets, list):
            return [str(b) for b in bullets[:3]]
    except json.JSONDecodeError:
        pass
    return [description[:300]]  # fallback: first 300 chars


def enrich_offer_detail(offer_detail: dict, cv_skills: list[str], model: str = "ollama/qwen2.5:7b", api_key: str | None = None) -> dict:
    """
    Build enriched skill tags from a full offer detail (which includes 'competences').
    Returns matched_skills (green) and missing_skills (red) using the LLM-filtered tech stack.
    """
    cv_skills_lower = [s.lower() for s in cv_skills]

    raw_competences = [
        c["libelle"]
        for c in offer_detail.get("competences", [])
        if c.get("exigence") in ("E", "S")
    ]
    tech_competences = filter_technical_skills(raw_competences, model=model, api_key=api_key)
    tech_set_lower = {s.lower() for s in tech_competences}

    offer_text = f"{offer_detail.get('intitule', '')} {offer_detail.get('description', '')}".lower()
    matched = [s for s in cv_skills if s.lower() in offer_text][:6]
    missing = [
        s for s in tech_competences
        if not any(cv_s in s.lower() or s.lower() in cv_s for cv_s in cv_skills_lower)
        and s.lower() in tech_set_lower
    ][:5]

    return {"matched_skills": matched, "missing_skills": missing}


def score_offers(offers: list[dict]) -> list[dict]:
    """
    Score each offer against the CV and GitHub repos using embedding similarity.
    Returns the offers sorted by relevance, each enriched with 'score' and 'github_matches'.
    """
    cv = get_latest_cv()
    cv_skills = cv.tech_skills or [] if cv else []
    cv_skills_lower = [s.lower() for s in cv_skills]

    offer_texts = [
        f"{offer.get('intitule', '')} {offer.get('description', '')[:1000]}"
        for offer in offers
    ]
    offer_embeddings = _embedding_model.encode(offer_texts, normalize_embeddings=True).tolist()

    if cv_rag._collection is None:
        cv_rag._collection = cv_rag.client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    if github_rag._collection is None:
        github_rag._collection = github_rag.client.get_or_create_collection(GITHUB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    cv_results = cv_rag._collection.query(
        query_embeddings=offer_embeddings,
        n_results=3,
        include=["distances", "metadatas"],
    )

    github_count = github_rag._collection.count()
    github_results = None
    if github_count > 0:
        github_results = github_rag._collection.query(
            query_embeddings=offer_embeddings,
            n_results=min(3, github_count),
            include=["distances", "metadatas"],
        )

    scored = []
    for i, offer in enumerate(offers):
        # CV score
        cv_distances = cv_results["distances"][i]
        avg_cv = sum(cv_distances) / len(cv_distances)
        score_cv = 1 / (1 + avg_cv)

        # GitHub score + matches
        score_github = 0.0
        github_matches = []
        if github_results:
            gh_distances = github_results["distances"][i]
            gh_metadatas = github_results["metadatas"][i]
            avg_gh = sum(gh_distances) / len(gh_distances)
            score_github = 1 / (1 + avg_gh)
            # Keep only repos closer than average (the genuinely relevant ones)
            github_matches = [
                gh_metadatas[j]["repo"]
                for j in range(len(gh_distances))
                if gh_distances[j] < avg_gh
            ]

        scored.append({
            **offer,
            "score": round(0.6 * score_cv + 0.4 * score_github, 4),
            "github_matches": github_matches,
            "matched_skills": tag_matched_skills(offer, cv_skills_lower),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
