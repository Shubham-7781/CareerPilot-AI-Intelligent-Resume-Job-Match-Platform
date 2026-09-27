import uuid
from datetime import datetime
from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: uuid.UUID
    original_filename: str
    full_name: str | None
    email: str | None
    phone: str | None
    parsed_sections: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    job_description: str | None = None
    job_role: str | None = None


class TailorRequest(BaseModel):
    job_description: str | None = None
    job_role: str | None = None
    extra_skills: str | None = None


class CourseRecommendation(BaseModel):
    title: str
    reason: str


class BulletRewrite(BaseModel):
    original: str
    improved: str


class AnalysisOut(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    ats_score: float
    keyword_match_score: float
    format_score: float
    section_score: float
    matched_skills: list[str] | None
    missing_skills: list[str] | None
    recommendations: list[str] | None

    resume_score: float | None = None
    overall_assessment: str | None = None
    strengths: list[str] | None = None
    improvements: list[str] | None = None
    skill_proficiency: dict[str, str] | None = None
    section_feedback: dict[str, str] | None = None
    course_recommendations: list[CourseRecommendation] | None = None
    job_match_analysis: str | None = None
    job_match_percentage: float | None = None
    job_requirements_not_met: list[str] | None = None
    bullet_rewrites: list[BulletRewrite] | None = None
    engine: str | None = None

    created_at: datetime

    class Config:
        from_attributes = True
