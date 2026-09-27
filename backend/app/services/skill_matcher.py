"""
Skill extraction.

The original approach (and a first pass here) used plain substring search
over a ~20-word list, which has two real problems: false positives from
substring matches inside unrelated words (e.g. "go" matching inside
"good", "r" matching inside almost anything), and no way to express
synonyms (e.g. "node" / "node.js" / "nodejs"). This uses spaCy's
PhraseMatcher, which matches on token boundaries, plus a categorized
taxonomy with common synonym variants folded into a canonical skill name.
"""
from app.services.resume_parser import get_nlp

SKILL_TAXONOMY: dict[str, list[str]] = {
    "python": ["python", "python3"],
    "java": ["java"],
    "javascript": ["javascript", "js", "es6"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp"],
    "go": ["golang", "go lang"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angular.js", "angularjs"],
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "spring boot": ["spring boot", "spring framework"],
    "sql": ["sql", "structured query language"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "github", "gitlab"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "rest api": ["rest api", "restful api", "rest apis"],
    "graphql": ["graphql"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "neural networks"],
    "nlp": ["nlp", "natural language processing"],
    "data analysis": ["data analysis", "data analytics"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "agile": ["agile", "scrum"],
    "communication": ["communication skills", "verbal communication"],
    "leadership": ["leadership", "team leadership"],
    "problem solving": ["problem solving", "problem-solving"],
    "project management": ["project management"],
}

_matcher = None
_canonical_by_match_id: dict[int, str] = {}


def _build_matcher():
    global _matcher, _canonical_by_match_id
    from spacy.matcher import PhraseMatcher

    nlp = get_nlp()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    canonical_by_match_id = {}

    for canonical, variants in SKILL_TAXONOMY.items():
        patterns = [nlp.make_doc(v) for v in variants]
        match_id = nlp.vocab.strings[canonical]
        matcher.add(canonical, patterns)
        canonical_by_match_id[match_id] = canonical

    _matcher = matcher
    _canonical_by_match_id = canonical_by_match_id
    return matcher, canonical_by_match_id


def extract_skills(text: str) -> list[str]:
    """Returns a de-duplicated, sorted list of canonical skill names found
    in the text, matched on token boundaries (not naive substring search)."""
    if not text:
        return []

    matcher, canonical_by_match_id = _build_matcher() if _matcher is None else (_matcher, _canonical_by_match_id)

    nlp = get_nlp()
    doc = nlp(text[:50_000])  # cap for very long resumes
    matches = matcher(doc)

    found = {canonical_by_match_id[match_id] for match_id, start, end in matches}
    return sorted(found)
