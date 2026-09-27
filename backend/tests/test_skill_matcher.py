from app.services.skill_matcher import extract_skills


def test_extracts_known_skills():
    text = "Experienced with Python, React, and PostgreSQL. Built REST APIs with FastAPI."
    skills = extract_skills(text)
    assert "python" in skills
    assert "react" in skills
    assert "postgresql" in skills
    assert "fastapi" in skills


def test_matches_synonyms_to_canonical_name():
    text = "Strong experience with Node.js and K8s deployments, using Mongo for storage."
    skills = extract_skills(text)
    assert "node.js" in skills
    assert "kubernetes" in skills
    assert "mongodb" in skills


def test_does_not_false_positive_on_substrings():
    # "go" should NOT match inside "good", "algorithm" should not trigger "go"
    text = "She has a good algorithm for solving problems and writes great code."
    skills = extract_skills(text)
    assert "go" not in skills


def test_empty_text_returns_empty_list():
    assert extract_skills("") == []
    assert extract_skills(None) == []
