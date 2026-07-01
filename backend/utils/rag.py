from sentence_transformers import SentenceTransformer
import chromadb
from litellm import completion
from cv_model import CVProfile

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # multilingual for French support
COLLECTION_NAME = "cv_index"


class CVRagIndex:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
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
        self._collection = self.client.create_collection(COLLECTION_NAME)

        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [{"section": c["section"]} for c in chunks]
        embeddings = self.model.encode(texts).tolist()

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

        query_embedding = self.model.encode([query_text]).tolist()
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


cv_rag = CVRagIndex()


def analyze_offer(
    offer: dict,
    retrieved_chunks: list[dict],
    model: str = "ollama/qwen2.5:7b",
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

    response = completion(model=model, messages=messages, temperature=0.3)
    return response.choices[0].message.content
