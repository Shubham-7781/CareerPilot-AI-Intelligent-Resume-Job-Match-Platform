import json
import re

import google.generativeai as genai

from app.core.config import settings

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


_PROMPT_TEMPLATE = """You are an expert resume writer. Rewrite the candidate's resume below into a
tailored, optimized version for the target job, using ONLY facts, projects, skills and experience that
are actually present in the original resume — never invent employers, titles, numbers, or projects that
aren't there. You may rephrase, reorder, emphasize, and tighten wording, and prioritize/re-surface the
candidate's existing skills that match the job. If the candidate explicitly lists additional skills they
have (provided separately below), you may include those too since the candidate confirmed they have them.

Respond with ONLY a single valid JSON object (no markdown fences, no commentary) matching this schema:

{{
  "full_name": "<candidate name>",
  "contact_line": "<email | phone | location, whatever is available, pipe-separated>",
  "summary": "<3-4 sentence professional summary tailored to the target job>",
  "skills": ["<skill>", "... ordered with most job-relevant first"],
  "experience": [
    {{"title": "<role/title>", "org": "<company/organization>", "dates": "<dates or empty string>",
      "bullets": ["<tailored, action-verb, quantified-where-possible bullet>", "..."]}}
  ],
  "projects": [
    {{"name": "<project name>", "link": "<url or empty string>",
      "bullets": ["<tailored bullet>", "..."]}}
  ],
  "education": [
    {{"institution": "<name>", "detail": "<degree, dates, gpa/percentage as available>"}}
  ],
  "certifications": ["<certification/course, if any>"]
}}

Leave "experience" as an empty list if the original resume has no work experience section — do not invent one.

Original resume text:
---
{resume_text}
---

Target role: {job_role}

Job description to tailor against:
---
{job_description}
---

Additional skills the candidate says they have (include naturally where relevant):
---
{extra_skills}
---

Respond with the JSON object only."""


def tailor_resume(
    raw_text: str,
    job_description: str | None,
    job_role: str | None,
    extra_skills: str | None,
) -> dict | None:
    model = _get_model()
    if model is None or not raw_text.strip():
        return None

    prompt = _PROMPT_TEMPLATE.format(
        resume_text=raw_text[:12000],
        job_role=job_role or "(not specified)",
        job_description=job_description or "(not specified — just tighten and improve the resume generally)",
        extra_skills=extra_skills or "(none provided)",
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        text = re.sub(r"^```json\s*|\s*```$", "", response.text.strip())
        data = json.loads(text)
    except Exception:
        return None

    return _cross_check_skills(data, raw_text, extra_skills)


def _cross_check_skills(data: dict, raw_text: str, extra_skills: str | None) -> dict:
    """Sanity-check Gemini's skill list against the source material using local
    semantic matching, rather than trusting the LLM's list blindly. Anything
    Gemini surfaced that isn't actually backed by the resume text or the
    candidate's self-declared extra skills gets dropped, so we never ship a
    tailored resume claiming a skill the candidate didn't provide evidence for.
    """
    skills = data.get("skills")
    if not isinstance(skills, list) or not skills:
        return data

    try:
        from app.services.semantic_matcher import semantic_missing_skills_check
    except Exception:
        return data

    source_text = raw_text + "\n" + (extra_skills or "")
    # semantic_missing_skills_check tells us which of `skills` are NOT
    # semantically supported by source_text — those are the ones to drop.
    unsupported = semantic_missing_skills_check(skills, source_text)
    if unsupported:
        data["skills"] = [s for s in skills if s not in unsupported]

    return data
