import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Heading1"], fontSize=20, textColor=colors.HexColor("#1e3a8a"), spaceAfter=4),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=11, textColor=colors.grey, spaceAfter=16),
        "heading": ParagraphStyle("Heading", parent=base["Heading2"], fontSize=13, textColor=colors.white,
                                   backColor=colors.HexColor("#1e3a8a"), spaceBefore=14, spaceAfter=8,
                                   leftIndent=4, borderPadding=(4, 4, 4, 4)),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontSize=10, leading=14, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base["Normal"], fontSize=10, leading=14, leftIndent=14,
                                  bulletIndent=4, spaceAfter=4),
    }


def build_analysis_pdf(candidate_name: str, filename: str, analysis: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    s = _styles()
    story = [
        Paragraph("CareerPilot Resume Analysis Report", s["title"]),
        Paragraph(f"{candidate_name or 'Candidate'} &middot; {filename}", s["subtitle"]),
    ]

    resume_score = analysis.get("resume_score") or analysis.get("ats_score") or 0
    ats_score = analysis.get("ats_score") or 0
    job_match = analysis.get("job_match_percentage")

    score_rows = [["Resume Score", "ATS Score"] + (["Job Match"] if job_match is not None else []),
                  [f"{round(resume_score)}/100", f"{round(ats_score)}/100"] + ([f"{round(job_match)}/100"] if job_match is not None else [])]
    score_table = Table(score_rows, colWidths=[1.8 * inch] * len(score_rows[0]))
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(score_table)

    def section(title, body_items):
        if not body_items:
            return
        story.append(Paragraph(title, s["heading"]))
        if isinstance(body_items, str):
            story.append(Paragraph(body_items, s["body"]))
        else:
            for item in body_items:
                story.append(Paragraph(f"&bull; {item}", s["bullet"]))

    section("Overall Assessment", analysis.get("overall_assessment"))
    section("Key Strengths", analysis.get("strengths"))
    section("Areas for Improvement", analysis.get("improvements"))

    section_feedback = analysis.get("section_feedback") or {}
    if section_feedback:
        story.append(Paragraph("Section-by-Section Feedback", s["heading"]))
        for k, v in section_feedback.items():
            story.append(Paragraph(f"<b>{k.capitalize()}:</b> {v}", s["body"]))

    matched = analysis.get("matched_skills") or []
    missing = analysis.get("missing_skills") or []
    if matched:
        section("Matched Skills", ", ".join(matched))
    if missing:
        section("Missing Skills", ", ".join(missing))

    bullet_rewrites = analysis.get("bullet_rewrites") or []
    if bullet_rewrites:
        story.append(Paragraph("Suggested Bullet Rewrites", s["heading"]))
        for r in bullet_rewrites:
            story.append(Paragraph(f"<b>Before:</b> {r.get('original', '')}", s["body"]))
            story.append(Paragraph(f"<b>After:</b> {r.get('improved', '')}", s["body"]))
            story.append(Spacer(1, 6))

    courses = analysis.get("course_recommendations") or []
    if courses:
        story.append(Paragraph("Recommended Courses & Certifications", s["heading"]))
        for c in courses:
            story.append(Paragraph(f"&bull; <b>{c.get('title', '')}</b> — {c.get('reason', '')}", s["bullet"]))

    if analysis.get("job_match_analysis"):
        section("Job Match Analysis", analysis["job_match_analysis"])
        not_met = analysis.get("job_requirements_not_met") or []
        if not_met:
            section("Requirements Not Clearly Met", not_met)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def build_tailored_resume_pdf(tailored: dict) -> bytes:
    """Renders a tailored resume (the JSON produced by resume_tailor.tailor_resume)
    as a clean, printable one-column resume PDF — not the analysis-report
    layout above, since this is meant to be sent to employers directly."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    base = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", parent=base["Heading1"], fontSize=20,
                                 textColor=colors.HexColor("#1e3a8a"), spaceAfter=2)
    contact_style = ParagraphStyle("Contact", parent=base["Normal"], fontSize=9.5,
                                    textColor=colors.grey, spaceAfter=14)
    heading_style = ParagraphStyle("Heading", parent=base["Heading2"], fontSize=12,
                                    textColor=colors.HexColor("#1e3a8a"), spaceBefore=12, spaceAfter=6,
                                    borderColor=colors.HexColor("#1e3a8a"), borderWidth=0, borderPadding=0)
    role_style = ParagraphStyle("Role", parent=base["Normal"], fontSize=10.5, leading=13, spaceAfter=1,
                                 textColor=colors.HexColor("#111827"))
    meta_style = ParagraphStyle("Meta", parent=base["Normal"], fontSize=9, leading=12,
                                 textColor=colors.grey, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=base["Normal"], fontSize=10, leading=14, spaceAfter=8)
    bullet_style = ParagraphStyle("Bullet", parent=base["Normal"], fontSize=9.5, leading=13,
                                   leftIndent=14, bulletIndent=4, spaceAfter=2)

    story = [
        Paragraph(tailored.get("full_name") or "Candidate", name_style),
    ]
    if tailored.get("contact_line"):
        story.append(Paragraph(tailored["contact_line"], contact_style))

    def hr():
        t = Table([[""]], colWidths=[6.6 * inch], rowHeights=[1])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a"))]))
        return t

    if tailored.get("summary"):
        story.append(Paragraph("Professional Summary", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        story.append(Paragraph(tailored["summary"], body_style))

    skills = tailored.get("skills") or []
    if skills:
        story.append(Paragraph("Skills", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        story.append(Paragraph(" &nbsp;&bull;&nbsp; ".join(skills), body_style))

    experience = tailored.get("experience") or []
    if experience:
        story.append(Paragraph("Experience", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        for job in experience:
            title = job.get("title", "")
            org = job.get("org", "")
            dates = job.get("dates", "")
            header = f"<b>{title}</b>" + (f" — {org}" if org else "")
            story.append(Paragraph(header, role_style))
            if dates:
                story.append(Paragraph(dates, meta_style))
            for b in job.get("bullets") or []:
                story.append(Paragraph(f"&bull; {b}", bullet_style))
            story.append(Spacer(1, 8))

    projects = tailored.get("projects") or []
    if projects:
        story.append(Paragraph("Projects", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        for proj in projects:
            name = proj.get("name", "")
            link = proj.get("link", "")
            header = f"<b>{name}</b>" + (f" — {link}" if link else "")
            story.append(Paragraph(header, role_style))
            for b in proj.get("bullets") or []:
                story.append(Paragraph(f"&bull; {b}", bullet_style))
            story.append(Spacer(1, 8))

    education = tailored.get("education") or []
    if education:
        story.append(Paragraph("Education", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        for edu in education:
            inst = edu.get("institution", "")
            detail = edu.get("detail", "")
            story.append(Paragraph(f"<b>{inst}</b>" + (f" — {detail}" if detail else ""), body_style))

    certifications = tailored.get("certifications") or []
    if certifications:
        story.append(Paragraph("Certifications", heading_style))
        story.append(hr())
        story.append(Spacer(1, 6))
        for c in certifications:
            story.append(Paragraph(f"&bull; {c}", bullet_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
