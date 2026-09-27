"""
Local, free semantic matching using sentence-transformers.

skill_matcher.py's PhraseMatcher is exact/token-boundary matching against a
fixed taxonomy — precise, but blind to anything not already in the taxonomy
and blind to paraphrase (e.g. "led a team of 5 engineers" vs a JD asking for
"leadership experience"). This module adds an embeddings-based layer that
catches that kind of semantic overlap. It's used two ways:

  1. As the core of the deterministic fallback engine's job-match scoring,
     when no GEMINI_API_KEY is configured (or the Gemini call fails).
  2. As a cross-check on Gemini's own output — a "missing skill" or
     "unsupported skill" claim only sticks if it's also backed by actual
     text similarity, not just the LLM's say-so.

Model: all-MiniLM-L6-v2 (~80MB, CPU-friendly, no API key, fully local/offline
after the first download). Every public function fails open (returns a
neutral/empty result) on any error — this is an enrichment layer, never a
hard dependency for the request to succeed.
"""

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _cosine_matrix(a, b):
    import numpy as np
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def semantic_similarity_score(text_a: str, text_b: str) -> float:
    """0-100 semantic similarity between two blocks of text (e.g. whole resume
    vs whole job description). Returns 0.0 if either is empty or the model
    can't be loaded."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        import numpy as np
        model = get_model()
        emb = model.encode([text_a[:5000], text_b[:5000]])
        sim = _cosine_matrix(np.array([emb[0]]), np.array([emb[1]]))[0][0]
        return round(float(max(0.0, min(1.0, sim))) * 100, 2)
    except Exception:
        return 0.0


def _resume_phrases(resume_text: str) -> list[str]:
    """Break the resume into line/bullet-level chunks — a skill is usually
    demonstrated within a single bullet or line, so that's the unit we
    compare each candidate skill/phrase against, rather than the document
    as a whole (which would wash out short, specific phrases)."""
    lines = [l.strip(" \t•-*") for l in resume_text.split("\n")]
    return [l for l in lines if len(l) > 3][:400]


def semantic_missing_skills_check(candidate_phrases: list[str], source_text: str, threshold: float = 0.5) -> list[str]:
    """Given a list of skill/phrase strings, return the subset that are NOT
    semantically supported by anything in source_text — i.e. genuinely
    missing/unsupported. Used both to find real gaps against a job
    description, and to cross-check an LLM's claimed skill list against the
    source resume text.

    Fails open: if the model can't load, returns [] (nothing flagged as
    missing) rather than blocking the caller.
    """
    if not candidate_phrases:
        return []

    phrases = _resume_phrases(source_text)
    if not phrases:
        return list(candidate_phrases)

    try:
        import numpy as np
        model = get_model()
        phrase_emb = np.array(model.encode(phrases))
        skill_emb = np.array(model.encode(candidate_phrases))
        sims = _cosine_matrix(skill_emb, phrase_emb)  # [n_skills, n_phrases]
        best = sims.max(axis=1)
        return [s for s, score in zip(candidate_phrases, best) if score < threshold]
    except Exception:
        return []


def semantic_jd_gap_analysis(resume_text: str, job_description: str, threshold: float = 0.5) -> tuple[list[str], list[str]]:
    """For a job description with no keyword-taxonomy hits at all, break it
    into requirement-ish lines and semantically check each against the
    resume. Returns (semantically_matched_lines, semantically_missing_lines).
    """
    if not job_description or not job_description.strip():
        return [], []

    jd_lines = [l.strip(" \t•-*") for l in job_description.split("\n") if len(l.strip()) > 8][:60]
    if not jd_lines:
        return [], []

    missing = semantic_missing_skills_check(jd_lines, resume_text, threshold=threshold)
    missing_set = set(missing)
    matched = [l for l in jd_lines if l not in missing_set]
    return matched, missing
