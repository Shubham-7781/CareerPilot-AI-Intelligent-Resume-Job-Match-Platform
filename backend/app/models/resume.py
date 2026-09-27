import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))

    # Structured extraction (normalized, not one giant blob)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(120), nullable=True)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_sections: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # education, experience, projects
    skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"technical": [...], "soft": [...]}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)

    ats_score: Mapped[float] = mapped_column(Float)
    keyword_match_score: Mapped[float] = mapped_column(Float)
    format_score: Mapped[float] = mapped_column(Float)
    section_score: Mapped[float] = mapped_column(Float)

    missing_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matched_skills: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Rich LLM-generated feedback (Gemini). Null when the deterministic
    # fallback engine was used instead (no GEMINI_API_KEY configured).
    resume_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    improvements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    skill_proficiency: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    section_feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    course_recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    job_match_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_match_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    job_requirements_not_met: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bullet_rewrites: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(20), nullable=True)

    job_description_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # if matched against a JD

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="analyses")
