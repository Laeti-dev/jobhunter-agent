"""
Diagnostic script: inspect raw cosine distances behind a match, for a real offer.
Not part of the app — run manually with `python check_matching.py` to debug matching quality.
"""

from utils.rag import cv_rag, github_rag, _embedding_model, COLLECTION_NAME, GITHUB_COLLECTION_NAME

OFFER = {
    "intitule": "AI Software Engineer",
    "description": """
En tant qu'AI Software Engineer, ta mission depasse le cadre du developpement traditionnel.
Tu concois et deploies des applications robustes, scalables et intelligentes.

Build & Architecture : Concevoir et developper des backends ultra-performants en Python et FastAPI.
Prompt Engineering & LLMOps : Maitriser et exploiter le plein potentiel des modeles d'Anthropic (Claude).
Integration & RAG : Mettre en place des architectures RAG avancees et connecter les LLMs aux bases de
donnees et API d'entreprise.

Tu as au moins 4 ans d'experience en Software Engineering.

Hard Skills incontournables :
Maitrise avancee de Python et du framework FastAPI.
Experience concrete avec l'API d'Anthropic et l'ecosysteme d'agents/frameworks
(LangChain, LlamaIndex, ou CrewAI).
Culture DevOps / Cloud.
""",
}

query_text = f"{OFFER['intitule']} {OFFER['description']}"
query_embedding = _embedding_model.encode([query_text], normalize_embeddings=True).tolist()

print("=" * 70)
print("CV — chunks les plus proches (distance cosinus : 0 = identique, 2 = oppose)")
print("=" * 70)
cv_collection = cv_rag.client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
cv_results = cv_collection.query(
    query_embeddings=query_embedding,
    n_results=cv_collection.count(),
    include=["distances", "metadatas", "documents"],
)
for dist, meta, doc in zip(cv_results["distances"][0], cv_results["metadatas"][0], cv_results["documents"][0]):
    similarity = 1 - dist
    print(f"\n[{meta['section']}] distance={dist:.4f}  similarite={similarity:.4f}")
    print(f"  {doc[:200]}")

print("\n" + "=" * 70)
print("GITHUB — repos les plus proches")
print("=" * 70)
gh_collection = github_rag.client.get_or_create_collection(GITHUB_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
count = gh_collection.count()
if count == 0:
    print("Aucun repo indexe.")
else:
    gh_results = gh_collection.query(
        query_embeddings=query_embedding,
        n_results=count,
        include=["distances", "metadatas"],
    )
    for dist, meta in zip(gh_results["distances"][0], gh_results["metadatas"][0]):
        similarity = 1 - dist
        print(f"[{meta['repo']}] distance={dist:.4f}  similarite={similarity:.4f}")

avg_cv = sum(cv_results["distances"][0][:3]) / 3
score_cv = 1 / (1 + avg_cv)
print(f"\nScore CV (comme dans score_offers, top-3 moyenne) = {score_cv:.4f}")
