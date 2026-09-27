import re
import pdfplumber
import docx
import spacy

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = spacy.blank("en")
    return _nlp


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")

SECTION_HEADERS = {
    "education": ["education", "academic background", "academic qualification", "academic qualifications"],
    "experience": [
        "experience", "work experience", "employment history", "professional experience",
        "internship", "internships", "work history",
    ],
    "projects": ["projects", "academic projects", "personal projects", "key projects"],
    "skills": [
        "skills", "technical skills", "core competencies", "key expertise", "expertise",
        "key skills", "skills & expertise", "skills and expertise", "competencies",
        "technical expertise", "areas of expertise",
    ],
}


def extract_text(file_path: str, ext: str) -> str:
    if ext == ".pdf":
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    elif ext == ".docx":
        d = docx.Document(file_path)
        return "\n".join(p.text for p in d.paragraphs)
    raise ValueError(f"Unsupported extension: {ext}")


def split_sections(text: str) -> dict[str, str]:
    lines = text.split("\n")
    sections: dict[str, list[str]] = {k: [] for k in SECTION_HEADERS}
    current = None

    for line in lines:
        stripped = line.strip().lower()
        matched_section = None
        for section, headers in SECTION_HEADERS.items():
            if any(stripped == h or stripped.startswith(h) for h in headers):
                matched_section = section
                break
        if matched_section:
            current = matched_section
            continue
        if current:
            sections[current].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def extract_contact_info(text: str) -> dict:
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
    }


def extract_name(text: str) -> str | None:
    nlp = get_nlp()
    doc = nlp(text[:500])  # name is almost always near the top
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    # fallback: first non-empty line
    for line in text.split("\n"):
        if line.strip():
            return line.strip()
    return None


def parse_resume(file_path: str, ext: str) -> dict:
    """Single entry point for resume parsing — consolidates what used to be
    three separate, inconsistent parsers into one pipeline."""
    text = extract_text(file_path, ext)
    contact = extract_contact_info(text)
    name = extract_name(text)
    sections = split_sections(text)

    return {
        "raw_text": text,
        "full_name": name,
        "email": contact["email"],
        "phone": contact["phone"],
        "parsed_sections": sections,
    }
