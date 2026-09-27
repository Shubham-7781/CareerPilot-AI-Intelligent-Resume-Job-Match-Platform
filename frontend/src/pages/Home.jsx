import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="hero">
      <h1>CareerPilot</h1>
      <p className="hero-sub">AI-powered resume analysis, ATS scoring, and job matching.</p>
      <div className="hero-actions">
        {user ? (
          <Link className="btn-primary" to="/dashboard">Go to Dashboard</Link>
        ) : (
          <>
            <Link className="btn-primary" to="/signup">Get Started</Link>
            <Link className="btn-secondary" to="/login">Log In</Link>
          </>
        )}
      </div>

      <div className="feature-grid">
        <div className="feature-box">
          <h3>Smart Parsing</h3>
          <p>NLP-based extraction of contact info, skills, and structured sections from PDF/DOCX resumes.</p>
        </div>
        <div className="feature-box">
          <h3>ATS Scoring</h3>
          <p>Keyword matching, section completeness, and formatting checks against real job descriptions.</p>
        </div>
        <div className="feature-box">
          <h3>Job Matching</h3>
          <p>Live job search so you can act on your analysis immediately.</p>
        </div>
      </div>
    </div>
  );
}
