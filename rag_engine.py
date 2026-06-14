# ----------------- RAG RETRIEVAL ENGINE -----------------
# Lightweight Retrieval-Augmented Generation layer.
# Uses TF-IDF + cosine similarity to retrieve the most relevant past
# winning hackathon projects for a given team's skill profile + theme,
# then feeds them as grounding context into the Gemini prompt.

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from knowledge_base import WINNING_PROJECTS, get_corpus_texts

# Build the TF-IDF index once at import time (small corpus, cheap to rebuild)
_corpus_texts = get_corpus_texts()
_vectorizer = TfidfVectorizer(stop_words='english')
_corpus_matrix = _vectorizer.fit_transform(_corpus_texts)


def retrieve_similar_projects(skills, theme, top_k=3):
    """
    Retrieve the top_k most relevant past winning projects given a team's
    skill set and chosen hackathon theme.

    Returns a list of dicts: {title, theme, summary, why_it_won, score}
    """
    query = f"{theme} {skills}"
    query_vec = _vectorizer.transform([query])
    sims = cosine_similarity(query_vec, _corpus_matrix)[0]

    ranked_indices = sims.argsort()[::-1][:top_k]

    results = []
    for idx in ranked_indices:
        if sims[idx] <= 0:
            continue
        project = WINNING_PROJECTS[idx]
        results.append({
            "title": project["title"],
            "theme": project["theme"],
            "summary": project["summary"],
            "why_it_won": project["why_it_won"],
            "score": round(float(sims[idx]) * 100, 1),
        })

    # Fallback: if nothing scored > 0 (very sparse query), return top_k anyway
    if not results:
        for idx in ranked_indices[:top_k]:
            project = WINNING_PROJECTS[idx]
            results.append({
                "title": project["title"],
                "theme": project["theme"],
                "summary": project["summary"],
                "why_it_won": project["why_it_won"],
                "score": 0.0,
            })

    return results


def build_rag_context_block(retrieved):
    """Formats retrieved projects into a text block for the LLM prompt."""
    if not retrieved:
        return "No similar past projects found."

    lines = []
    for r in retrieved:
        lines.append(
            f"- \"{r['title']}\" ({r['theme']}): {r['summary']} "
            f"Why it won: {r['why_it_won']}"
        )
    return "\n".join(lines)
