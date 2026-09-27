import { useState } from "react";
import { jobsApi } from "../api/resources";

export default function JobSearch() {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSearched(true);
    try {
      const { data } = await jobsApi.search(query, location);
      setJobs(data.results);
    } catch (err) {
      if (err.response?.status === 503) {
        setError("Job search isn't configured yet — add Adzuna API credentials on the backend.");
      } else {
        setError("Job search failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <h1>Find Matching Jobs</h1>

      <form className="job-search-form" onSubmit={handleSearch}>
        <input
          placeholder="Job title, e.g. Backend Developer"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <input
          placeholder="Location, e.g. Bangalore"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      <div className="job-list">
        {jobs.map((job, i) => (
          <a className="job-card" href={job.url} target="_blank" rel="noreferrer" key={i}>
            <h3>{job.title}</h3>
            <p>{job.company} — {job.location}</p>
            {(job.salary_min || job.salary_max) && (
              <p className="muted">
                {job.salary_min ? `₹${Math.round(job.salary_min)}` : ""}
                {job.salary_max ? ` - ₹${Math.round(job.salary_max)}` : ""}
              </p>
            )}
          </a>
        ))}
      </div>

      {searched && !loading && !error && jobs.length === 0 && <p>No jobs found. Try different keywords.</p>}
    </div>
  );
}
