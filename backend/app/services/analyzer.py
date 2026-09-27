import json
import re

import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.services.skill_matcher import extract_skills

SECTION_WEIGHTS = {"education": 15, "experience": 40, "projects": 25, "skills": 20}

_MODEL_NAME = "gemini-2.5-flash"
_configured = False


def _get_model():
    global _configured
    if not settings.GEMINI_API_KEY:
        return None
    if not _configured:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True
    return genai.GenerativeModel(_MODEL_NAME)


# ---------------------------------------------------------------------------
# Deterministic fallback (used if no API key is configured, or the LLM call
# fails). This is the old heuristic engine — kept as a safety net, never the
# primary path when Gemini is available.
# ---------------------------------------------------------------------------

def _keyword_match_score(resume_text: str, job_description: str | None) -> tuple[float, list[str], list[str]]:
    if not job_description:
        return 0.0, [], []
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))
    if not jd_skills:
        # No taxonomy hits in the JD at all — fall back to local semantic
        # similarity (sentence-transformers) instead of pure keyword overlap,
        # so a JD written in prose still gets a meaningful score rather than 0.
        try:
            from app.services.semantic_matcher import semantic_similarity_score
            sem_score = semantic_similarity_score(resume_text, job_description)
        except Exception:
            sem_score = 0.0
        if sem_score > 0:
            return sem_score, [], []
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([resume_text, job_description])
        score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0]) * 100
        return round(score, 2), [], []
    matched = jd_skills & resume_skills
    missing = jd_skills - resume_skills
    # Cross-check: a "missing" skill might just be phrased differently in the
    # resume than in our fixed taxonomy/synonym list (e.g. "led cross-functional
    # squads" vs "leadership"). Recover those via embedding similarity instead
    # of penalizing the candidate for a wording mismatch the taxonomy can't see.
    if missing:
        try:
            from app.services.semantic_matcher import semantic_missing_skills_check
            still_missing = set(semantic_missing_skills_check(sorted(missing), resume_text))
            matched = matched | (missing - still_missing)
            missing = still_missing
        except Exception:
            pass
    score = (len(matched) / len(jd_skills)) * 100 if jd_skills else 0.0
    return round(score, 2), sorted(matched), sorted(missing)


def _section_completeness_score(sections: dict[str, str]) -> float:
    score = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        if sections.get(section, "").strip():
            score += weight
    return round(score, 2)


def _format_score(raw_text: str) -> float:
    word_count = len(raw_text.split())
    if word_count < 100:
        return 40.0
    if word_count > 1200:
        return 70.0
    return 90.0


def _fallback_analysis(raw_text: str, sections: dict[str, str], job_description: str | None) -> dict:
    kw_score, matched, missing = _keyword_match_score(raw_text, job_description)
    sect_score = _section_completeness_score(sections)
    fmt_score = _format_score(raw_text)

    ats = round(kw_score * 0.5 + sect_score * 0.3 + fmt_score * 0.2, 2) if job_description \
        else round(sect_score * 0.6 + fmt_score * 0.4, 2)

    recommendations = []
    if sect_score < 100:
        missing_sections = [s for s, w in SECTION_WEIGHTS.items() if not sections.get(s, "").strip()]
        recommendations.append(f"Add or expand these sections: {', '.join(missing_sections)}")
    if missing:
        recommendations.append(f"Consider adding these keywords from the job description: {', '.join(missing[:8])}")
    if fmt_score < 90:
        recommendations.append("Resume length looks off — aim for 1-2 pages of well-structured content.")

    return {
        "ats_score": ats,
        "keyword_match_score": kw_score,
        "format_score": fmt_score,
        "section_score": sect_score,
        "resume_score": ats,
        "matched_skills": matched,
        "missing_skills": missing,
        "recommendations": recommendations,
        "overall_assessment": None,
        "strengths": None,
        "improvements": None,
        "skill_proficiency": None,
        "course_recommendations": None,
        "job_match_analysis": None,
        "bullet_rewrites": None,
        "engine": "heuristic",
    }


# ---------------------------------------------------------------------------
# Gemini-powered analysis (primary path)
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """You are an expert resume analyst and career coach with deep knowledge of hiring
practices, ATS systems, and industry standards across fields. Analyze the resume below thoroughly and
respond with ONLY a single valid JSON object (no markdown fences, no commentary before or after) matching
exactly this schema:

{{
  "resume_score": <int 0-100, overall quality>,
  "ats_score": <int 0-100, how well it would survive an Applicant Tracking System>,
  "overall_assessment": "<3-5 sentence summary of quality, formatting, and impression>",
  "strengths": ["<specific strength 1>", "... 5-7 items, each a full sentence with concrete reasoning"],
  "improvements": ["<specific, actionable improvement 1>", "... 5-7 items, each a full sentence"],
  "matched_skills": ["<skill the resume demonstrates>", "..."],
  "missing_skills": ["<skill that would strengthen it for the target role/JD>", "..."],
  "skill_proficiency": {{"<skill>": "<beginner|intermediate|advanced, inferred from resume>"}},
  "section_feedback": {{
    "experience": "<2-3 sentences: use of action verbs, quantified impact, relevance>",
    "education": "<2-3 sentences>",
    "projects": "<2-3 sentences>",
    "skills": "<2-3 sentences>"
  }},
  "course_recommendations": [
    {{"title": "<course/certification name>", "reason": "<why it helps>"}}
  ],
  "job_match_analysis": "<null if no job description given, else 2-4 sentences on fit>",
  "job_match_percentage": <int 0-100 or null if no job description given>,
  "job_requirements_not_met": ["<gap from the JD>", "... or empty list"],
  "bullet_rewrites": [
    {{"original": "<a weak bullet/line copied verbatim from the resume>", "improved": "<a stronger rewrite using an action verb and, where plausible, a quantified impact>"}}
  ]
}}

Scoring guidance: a resume with significant issues should score below 60, an average resume 60-75, a good
resume 75-85, an excellent resume 85-100. Be specific and reference actual content from the resume — never
generic filler. For bullet_rewrites, pick 4-6 of the weakest experience/project bullets and rewrite them —
copy "original" verbatim from the resume text.

Resume text:
---
{resume_text}
---
{role_block}{jd_block}
Respond with the JSON object only."""


def _run_gemini_analysis(raw_text: str, job_role: str | None, job_description: str | None) -> dict | None:
    model = _get_model()
    if model is None:
        return None

    role_block = f"\nThe candidate is targeting this role: {job_role}\n" if job_role else ""
    jd_block = (
        f"\nCompare the resume against this job description and fill in the job_match fields:\n---\n{job_description}\n---\n"
        if job_description else "\n"
    )

    prompt = _PROMPT_TEMPLATE.format(resume_text=raw_text[:12000], role_block=role_block, jd_block=jd_block)

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        text = response.text.strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
        data = json.loads(text)
    except Exception:
        return None

    return data


def run_analysis(
    raw_text: str,
    sections: dict[str, str],
    job_description: str | None = None,
    job_role: str | None = None,
) -> dict:
    llm_result = _run_gemini_analysis(raw_text, job_role, job_description) if raw_text.strip() else None

    if llm_result is None:
        return _fallback_analysis(raw_text, sections, job_description)

    resume_score = llm_result.get("resume_score", 0)
    ats_score = llm_result.get("ats_score", 0)

    matched_skills = llm_result.get("matched_skills") or []
    missing_skills = llm_result.get("missing_skills") or []
    # Cross-check Gemini's "missing_skills" against the resume text with local
    # semantic matching — the LLM can miss that a skill is actually present
    # just because it's phrased differently than the JD's wording. Anything
    # semantically supported gets moved from missing to matched.
    if missing_skills:
        try:
            from app.services.semantic_matcher import semantic_missing_skills_check
            still_missing = set(semantic_missing_skills_check(missing_skills, raw_text))
            recovered = [s for s in missing_skills if s not in still_missing]
            if recovered:
                matched_skills = list(dict.fromkeys(matched_skills + recovered))
                missing_skills = [s for s in missing_skills if s in still_missing]
        except Exception:
            pass

    return {
        "ats_score": float(ats_score or 0),
        "keyword_match_score": float(llm_result.get("job_match_percentage") or 0),
        "format_score": _format_score(raw_text),
        "section_score": _section_completeness_score(sections),
        "resume_score": float(resume_score or 0),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": llm_result.get("improvements") or [],
        "overall_assessment": llm_result.get("overall_assessment"),
        "strengths": llm_result.get("strengths") or [],
        "improvements": llm_result.get("improvements") or [],
        "skill_proficiency": llm_result.get("skill_proficiency") or {},
        "section_feedback": llm_result.get("section_feedback") or {},
        "course_recommendations": llm_result.get("course_recommendations") or [],
        "job_match_analysis": llm_result.get("job_match_analysis"),
        "job_match_percentage": llm_result.get("job_match_percentage"),
        "job_requirements_not_met": llm_result.get("job_requirements_not_met") or [],
        "bullet_rewrites": llm_result.get("bullet_rewrites") or [],
        "engine": "gemini",
    }
