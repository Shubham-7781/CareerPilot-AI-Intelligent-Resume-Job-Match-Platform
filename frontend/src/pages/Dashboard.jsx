import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { resumeApi } from "../api/resources";

export default function Dashboard() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    resumeApi
      .list()
      .then(({ data }) => setResumes(data))
      .catch(() => setError("Could not load your resumes."))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id) => {
    if (!confirm("Delete this resume?")) return;
    await resumeApi.remove(id);
    setResumes((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="page-container">
      <div className="page-header-row">
        <h1>Your Resumes</h1>
        <Link className="btn-primary-sm" to="/upload">+ Upload New</Link>
      </div>

      {loading && <p>Loading...</p>}
      {error && <div className="error-banner">{error}</div>}

      {!loading && resumes.length === 0 && (
        <div className="empty-state">
          <p>No resumes yet.</p>
          <Link className="btn-primary" to="/upload">Upload your first resume</Link>
        </div>
      )}

      <div className="resume-grid">
        {resumes.map((r) => (
          <div className="resume-card" key={r.id}>
            <h3>{r.original_filename}</h3>
            <p>{r.full_name || "Name not detected"}</p>
            <p className="muted">{r.email || "-"}</p>
            <div className="card-actions">
              <Link to={`/resumes/${r.id}`}>View & Analyze</Link>
              <button className="btn-link danger" onClick={() => handleDelete(r.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
