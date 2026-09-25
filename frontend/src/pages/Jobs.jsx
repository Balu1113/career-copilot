import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  MapPin,
  Building2,
  BriefcaseBusiness,
  ExternalLink,
  Bookmark,
  Loader2,
  AlertCircle,
} from "lucide-react";
import api from "../services/api";
import "../styles/jobs.css";

const Jobs = () => {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("Hyderabad");

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  const searchJobs = async (event) => {
    event?.preventDefault();

    if (!title.trim() && !location.trim()) {
      setError("Enter a job title or location.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams();

      if (title.trim()) {
        params.append("title", title.trim());
      }

      if (location.trim()) {
        params.append("location", location.trim());
      }

      params.append("limit", "10");

      const response = await api.get(`/jobs/search/?${params.toString()}`);

      setJobs(response.data?.jobs || []);
      setSearched(true);
    } catch (err) {
      console.error(err);

      setJobs([]);
      setError(
        err?.response?.data?.detail ||
          "Unable to search jobs. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const openJob = (job) => {
    if (!job.apply_link) {
      return;
    }

    window.open(job.apply_link, "_blank", "noopener,noreferrer");
  };

  const saveJob = async (job) => {
    try {
      await api.post("/jobs/", {
        company: job.company || "",
        job_title: job.title || "",
        job_url: job.apply_link || "",
        status: "saved",
      });

      alert("Job saved successfully.");
    } catch (err) {
      console.error(err);

      alert(err?.response?.data?.detail || "Unable to save this job.");
    }
  };

  return (
    <div className="jobs-page">
      <div className="jobs-page-header">
        <div>
          <h1>Jobs</h1>
          <p>
            Find real job opportunities in India and match them with your career
            profile.
          </p>
        </div>
      </div>

      <form className="jobs-search-card" onSubmit={searchJobs}>
        <div className="jobs-search-field">
          <Search size={18} />

          <input
            type="text"
            placeholder="Job title, skills or keywords"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>

        <div className="jobs-search-field">
          <MapPin size={18} />

          <input
            type="text"
            placeholder="Location"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
          />
        </div>

        <button type="submit" className="jobs-search-button" disabled={loading}>
          {loading ? (
            <>
              <Loader2 size={17} className="jobs-spinner" />
              Searching...
            </>
          ) : (
            <>
              <Search size={17} />
              Search Jobs
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="jobs-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="jobs-loading">
          <Loader2 size={28} className="jobs-spinner" />
          <p>Finding real Indian job listings...</p>
        </div>
      )}

      {!loading && searched && !error && (
        <div className="jobs-results-header">
          <div>
            <h2>Job Opportunities</h2>
            <p>
              {jobs.length} jobs found
              {location ? ` in ${location}` : ""}
            </p>
          </div>
        </div>
      )}

      {!loading && searched && !error && jobs.length === 0 && (
        <div className="jobs-empty">
          <BriefcaseBusiness size={38} />
          <h3>No jobs found</h3>
          <p>Try another job title, skill or location.</p>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="jobs-list">
          {jobs.map((job, index) => (
            <div
              className="job-card"
              key={job.id || `${job.company}-${job.title}-${index}`}
            >
              <div className="job-card-main">
                <div className="job-company-icon">
                  <Building2 size={22} />
                </div>

                <div className="job-content">
                  <h3>{job.title || "Job Position"}</h3>

                  <div className="job-company">
                    {job.company || "Company not specified"}
                  </div>

                  <div className="job-meta">
                    {job.location && (
                      <span>
                        <MapPin size={15} />
                        {job.location}
                      </span>
                    )}

                    {job.job_type && (
                      <span>
                        <BriefcaseBusiness size={15} />
                        {job.job_type}
                      </span>
                    )}

                    {job.experience && (
                      <span>Experience: {job.experience}</span>
                    )}
                  </div>

                  {job.skills && (
                    <div className="job-skills">
                      <strong>Skills:</strong> {job.skills}
                    </div>
                  )}

                  {job.description && (
                    <p className="job-description">
                      {job.description.length > 350
                        ? `${job.description.slice(0, 350)}...`
                        : job.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="job-card-actions">
                <button
                  type="button"
                  className="job-save-button"
                  onClick={() => saveJob(job)}
                >
                  <Bookmark size={16} />
                  Save
                </button>

                <button
                  type="button"
                  className="job-analyze-button"
                  onClick={() =>
                    navigate("/career-analysis", {
                      state: {
                        jobDescription: [
                          job.description,
                          job.responsibilities,
                          job.skills,
                          job.experience,
                          job.about_company,
                        ]
                          .filter(Boolean)
                          .join("\n\n"),

                        jobTitle: job.title || "",

                        company: job.company || "",

                        location: job.location || "",

                        jobType: job.job_type || "",

                        experience: job.experience || "",

                        jobUrl: job.apply_link || "",

                        postedDate: job.posted_date || "",

                        source: job.source || "IndianAPI",
                      },
                    })
                  }
                >
                  Analyze
                </button>

                <button
                  type="button"
                  className="job-apply-button"
                  onClick={() => openJob(job)}
                  disabled={!job.apply_link}
                >
                  <ExternalLink size={16} />
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!searched && !loading && (
        <div className="jobs-initial-state">
          <BriefcaseBusiness size={48} />

          <h2>Find your next opportunity</h2>

          <p>Search real job listings from companies hiring in India.</p>
        </div>
      )}
    </div>
  );
};

export default Jobs;
