import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { resumeApi } from "../api/resources";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const { data } = await resumeApi.upload(file);
      navigate(`/resumes/${data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try a PDF or DOCX under 5MB.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-container">
      <h1>Upload Your Resume</h1>
      <p className="subtitle">PDF or DOCX, up to 5MB</p>

      <form className="upload-card" onSubmit={handleSubmit}>
        {error && <div className="error-banner">{error}</div>}

        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files[0])}
          required
        />

        <button className="btn-primary" type="submit" disabled={uploading || !file}>
          {uploading ? "Uploading & parsing..." : "Upload & Analyze"}
        </button>
      </form>
    </div>
  );
}
