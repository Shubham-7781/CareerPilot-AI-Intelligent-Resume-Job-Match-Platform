import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume, Analysis
from app.schemas.resume import ResumeOut, AnalysisRequest, AnalysisOut, TailorRequest
from app.services.file_validation import validate_and_save_upload
from app.services.resume_parser import parse_resume
from app.services.analyzer import run_analysis
from app.services.resume_tailor import tailor_resume
from app.services.pdf_report import build_analysis_pdf, build_tailored_resume_pdf

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    save_path, ext = validate_and_save_upload(file)

    try:
        parsed = parse_resume(save_path, ext)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not parse this resume. Please check the file and try again.",
        )

    resume = Resume(
        owner_id=current_user.id,
        original_filename=file.filename,
        file_path=save_path,
        file_type=ext,
        full_name=parsed["full_name"],
        email=parsed["email"],
        phone=parsed["phone"],
        raw_text=parsed["raw_text"],
        parsed_sections=parsed["parsed_sections"],
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Resume).filter(Resume.owner_id == current_user.id).order_by(Resume.created_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    db.delete(resume)
    db.commit()


@router.post("/{resume_id}/analyze", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def analyze_resume(
    resume_id: uuid.UUID,
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    result = run_analysis(
        resume.raw_text or "",
        resume.parsed_sections or {},
        payload.job_description,
        payload.job_role or resume.target_role,
    )

    analysis = Analysis(
        resume_id=resume.id,
        ats_score=result["ats_score"],
        keyword_match_score=result["keyword_match_score"],
        format_score=result["format_score"],
        section_score=result["section_score"],
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        recommendations=result["recommendations"],
        resume_score=result.get("resume_score"),
        overall_assessment=result.get("overall_assessment"),
        strengths=result.get("strengths"),
        improvements=result.get("improvements"),
        skill_proficiency=result.get("skill_proficiency"),
        section_feedback=result.get("section_feedback"),
        course_recommendations=result.get("course_recommendations"),
        job_match_analysis=result.get("job_match_analysis"),
        job_match_percentage=result.get("job_match_percentage"),
        job_requirements_not_met=result.get("job_requirements_not_met"),
        bullet_rewrites=result.get("bullet_rewrites"),
        engine=result.get("engine"),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/{resume_id}/analyses/{analysis_id}/report")
def download_analysis_report(
    resume_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    analysis = db.get(Analysis, analysis_id)
    if not analysis or analysis.resume_id != resume.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    payload = {
        "resume_score": analysis.resume_score,
        "ats_score": analysis.ats_score,
        "job_match_percentage": analysis.job_match_percentage,
        "overall_assessment": analysis.overall_assessment,
        "strengths": analysis.strengths,
        "improvements": analysis.improvements,
        "section_feedback": analysis.section_feedback,
        "matched_skills": analysis.matched_skills,
        "missing_skills": analysis.missing_skills,
        "bullet_rewrites": analysis.bullet_rewrites,
        "course_recommendations": analysis.course_recommendations,
        "job_match_analysis": analysis.job_match_analysis,
        "job_requirements_not_met": analysis.job_requirements_not_met,
    }
    pdf_bytes = build_analysis_pdf(resume.full_name, resume.original_filename, payload)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{resume.original_filename}-analysis.pdf"'},
    )


@router.post("/{resume_id}/tailor")
def generate_tailored_resume(
    resume_id: uuid.UUID,
    payload: TailorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    tailored = tailor_resume(
        resume.raw_text or "",
        payload.job_description,
        payload.job_role or resume.target_role,
        payload.extra_skills,
    )
    if tailored is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tailored resume generation requires a GEMINI_API_KEY to be configured on the backend.",
        )

    pdf_bytes = build_tailored_resume_pdf(tailored)
    safe_name = (tailored.get("full_name") or resume.full_name or "resume").strip().replace(" ", "-")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}-tailored-resume.pdf"'},
    )
