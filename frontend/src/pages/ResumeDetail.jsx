import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { resumeApi } from "../api/resources";

export default function ResumeDetail() {
  const { id } = useParams();
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jobRole, setJobRole] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [extraSkills, setExtraSkills] = useState("");
  const [tailoring, setTailoring] = useState(false);
  const [tailorError, setTailorError] = useState("");

  useEffect(() => {
    resumeApi.get(id).then(({ data }) => setResume(data)).catch(() => setError("Resume not found."));
  }, [id]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError("");
    try {
      const { data } = await resumeApi.analyze(id, jobDescription, jobRole);
      setAnalysis(data);
    } catch {
      setError("Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleTailor = async () => {
    setTailoring(true);
    setTailorError("");
    try {
      const res = await resumeApi.tailor(id, jobDescription, jobRole, extraSkills);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "tailored-resume.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      if (err?.response?.status === 503) {
        setTailorError("Tailored resume generation needs a GEMINI_API_KEY configured on the backend.");
      } else {
        setTailorError("Couldn't generate a tailored resume. Please try again.");
      }
    } finally {
      setTailoring(false);
    }
  };

  if (error && !resume) return <div className="page-container"><div className="error-banner">{error}</div></div>;
  if (!resume) return <div className="page-container">Loading...</div>;

  return (
    <div className="page-container">
      <h1>{resume.original_filename}</h1>
      <div className="detail-grid">
        <div>
          <h3>Extracted Info</h3>
          <p><strong>Name:</strong> {resume.full_name || "-"}</p>
          <p><strong>Email:</strong> {resume.email || "-"}</p>
          <p><strong>Phone:</strong> {resume.phone || "-"}</p>

          <h3>Sections Found</h3>
          {resume.parsed_sections &&
            Object.entries(resume.parsed_sections).map(([section, text]) => (
              <details key={section}>
                <summary>{section} {text ? "✓" : "✗ missing"}</summary>
                <pre className="section-text">{text || "Not found"}</pre>
              </details>
            ))}
        </div>

        <div>
          <h3>AI Resume Analysis</h3>
          <input
            className="text-input"
            placeholder="Target role, e.g. Senior Backend Engineer (optional)"
            value={jobRole}
            onChange={(e) => setJobRole(e.target.value)}
          />
          <textarea
            placeholder="Paste a job description here to score against it (optional)"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={6}
          />
          <button className="btn-primary" onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? "Analyzing... (can take 10-20s)" : "Run Analysis"}
          </button>

          {error && <div className="error-banner">{error}</div>}

          {analysis && <AnalysisResult analysis={analysis} resumeId={id} />}

          <div className="analysis-section" style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid #e5e7eb" }}>
            <h3>Generate Tailored Resume</h3>
            <p style={{ color: "#6b7280", fontSize: 14, marginTop: -4, marginBottom: 10 }}>
              Rewrites your resume for the target role/job description above, using only what's in your
              original resume plus any extra skills you confirm below. Downloads as a PDF.
            </p>
            <textarea
              placeholder="Any additional skills you have that aren't on your resume yet (optional)"
              value={extraSkills}
              onChange={(e) => setExtraSkills(e.target.value)}
              rows={3}
            />
            <button className="btn-primary" onClick={handleTailor} disabled={tailoring}>
              {tailoring ? "Generating... (can take 10-20s)" : "Generate Tailored Resume (PDF)"}
            </button>
            {tailorError && <div className="error-banner">{tailorError}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

function AnalysisResult({ analysis, resumeId }) {
  const handleDownload = async () => {
    const res = await resumeApi.downloadReport(resumeId, analysis.id);
    const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "resume-analysis-report.pdf");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="analysis-result">
      {analysis.engine === "heuristic" && (
        <div className="notice-banner">
          Running on the basic keyword-matching engine — add a GEMINI_API_KEY on the backend for full
          in-depth AI analysis (strengths, improvements, course suggestions, and more).
        </div>
      )}

      <button className="btn-secondary" onClick={handleDownload} style={{ marginBottom: 16 }}>
        Download PDF Report
      </button>

      <div className="score-row">
        <ScoreBadge label="Resume Score" value={analysis.resume_score ?? analysis.ats_score} />
        <ScoreBadge label="ATS Score" value={analysis.ats_score} />
        {analysis.job_match_percentage != null && (
          <ScoreBadge label="Job Match" value={analysis.job_match_percentage} />
        )}
        <ScoreBadge label="Sections" value={analysis.section_score} />
      </div>

      {analysis.overall_assessment && (
        <Section title="Overall Assessment">
          <p>{analysis.overall_assessment}</p>
        </Section>
      )}

      {analysis.job_match_analysis && (
        <Section title="Job Match Analysis">
          <p>{analysis.job_match_analysis}</p>
          {analysis.job_requirements_not_met?.length > 0 && (
            <>
              <h4>Requirements not clearly met</h4>
              <ul>{analysis.job_requirements_not_met.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </>
          )}
        </Section>
      )}

      {analysis.strengths?.length > 0 && (
        <Section title="Key Strengths">
          <ul>{analysis.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </Section>
      )}

      {analysis.improvements?.length > 0 && (
        <Section title="Areas for Improvement">
          <ul>{analysis.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </Section>
      )}

      {analysis.section_feedback && Object.keys(analysis.section_feedback).length > 0 && (
        <Section title="Section-by-Section Feedback">
          {Object.entries(analysis.section_feedback).map(([k, v]) => (
            <p key={k}><strong>{cap(k)}:</strong> {v}</p>
          ))}
        </Section>
      )}

      {analysis.matched_skills?.length > 0 && (
        <Section title="Matched Skills">
          <div className="tag-list">
            {analysis.matched_skills.map((s) => <span className="tag tag-good" key={s}>{s}</span>)}
          </div>
        </Section>
      )}

      {analysis.missing_skills?.length > 0 && (
        <Section title="Missing Skills">
          <div className="tag-list">
            {analysis.missing_skills.map((s) => <span className="tag tag-warn" key={s}>{s}</span>)}
          </div>
        </Section>
      )}

      {analysis.skill_proficiency && Object.keys(analysis.skill_proficiency).length > 0 && (
        <Section title="Skill Proficiency">
          <div className="tag-list">
            {Object.entries(analysis.skill_proficiency).map(([skill, level]) => (
              <span className="tag" key={skill}>{skill}: {level}</span>
            ))}
          </div>
        </Section>
      )}

      {analysis.bullet_rewrites?.length > 0 && (
        <Section title="Suggested Bullet Rewrites">
          {analysis.bullet_rewrites.map((r, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <p><strong>Before:</strong> {r.original}</p>
              <p><strong>After:</strong> {r.improved}</p>
            </div>
          ))}
        </Section>
      )}

      {analysis.course_recommendations?.length > 0 && (
        <Section title="Recommended Courses & Certifications">
          <ul>
            {analysis.course_recommendations.map((c, i) => (
              <li key={i}><strong>{c.title}</strong> — {c.reason}</li>
            ))}
          </ul>
        </Section>
      )}

      {analysis.recommendations?.length > 0 && !analysis.improvements?.length && (
        <Section title="Recommendations">
          <ul>{analysis.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="analysis-section">
      <h4>{title}</h4>
      {children}
    </div>
  );
}

function cap(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function ScoreBadge({ label, value }) {
  const color = value >= 75 ? "good" : value >= 50 ? "warn" : "bad";
  return (
    <div className={`score-badge score-${color}`}>
      <div className="score-value">{Math.round(value)}</div>
      <div className="score-label">{label}</div>
    </div>
  );
}
