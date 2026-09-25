import { useEffect, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  ExternalLink,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./RecommendedJobs.css";

function RecommendedJobs() {
  const location = useLocation();
  const navigate = useNavigate();

  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState(location.state?.resumeId || "");
  const [resumeType, setResumeType] = useState(
    location.state?.resumeType || "uploaded",
  );

  const [locationName, setLocationName] = useState(
    location.state?.location || "Hyderabad",
  );

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const loadResumes = async () => {
      try {
        setLoadingResumes(true);
        setError("");

        const [uploadedResponse, generatedResponse] = await Promise.all([
          api.get("/resumes/"),
          api.get("/resume-builder/resumes/"),
        ]);

        const uploaded = uploadedResponse.data.map((resume) => ({
          ...resume,
          type: "uploaded",
          value: `uploaded:${resume.id}`,
          label: resume.title,
        }));

        const generated = generatedResponse.data
          .filter(
            (resume) =>
              resume.content && Object.keys(resume.content).length > 0,
          )
          .map((resume) => ({
            ...resume,
            type: "generated",
            value: `generated:${resume.id}`,
            label: resume.title,
          }));

        const combined = [...uploaded, ...generated];

        setResumes(combined);

        if (location.state?.resumeId) {
          const incoming = String(location.state.resumeId);

          const matchingResume = combined.find(
            (resume) =>
              resume.value === incoming || String(resume.id) === incoming,
          );

          if (matchingResume) {
            setResumeId(matchingResume.value);
            setResumeType(matchingResume.type);
          }
        } else if (combined.length > 0) {
          setResumeId(combined[0].value);
          setResumeType(combined[0].type);
        }
      } catch (err) {
        console.error(err);
        setError("Unable to load your resumes.");
      } finally {
        setLoadingResumes(false);
      }
    };

    loadResumes();
  }, [location.state]);

  const handleResumeChange = (event) => {
    const value = event.target.value;

    setResumeId(value);

    const [type] = value.split(":");

    setResumeType(type || "uploaded");
  };

  const getMatchClass = (percentage) => {
    if (percentage >= 80) {
      return "match-high";
    }

    if (percentage >= 60) {
      return "match-medium";
    }

    return "match-low";
  };

  const searchRecommendedJobs = async () => {
    if (!resumeId) {
      setError("Please select a resume.");
      return;
    }

    const [, selectedId] = String(resumeId).split(":");

    if (!selectedId) {
      setError("Invalid resume selection.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await api.get("/jobs/recommended/", {
        params: {
          resume_id: selectedId,
          resume_type: resumeType,
          location: locationName.trim(),
          limit: 10,
        },
      });

      setJobs(response.data.jobs || []);
      setSearched(true);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail || "Unable to load recommended jobs.",
      );

      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeJob = (job) => {
    const jobDescription = [
      job.description,
      job.responsibilities,
      job.skills,
      job.experience,
      job.about_company,
    ]
      .filter(Boolean)
      .join("\n\n");

    navigate("/career-analysis", {
      state: {
        resumeId,
        resumeType,
        jobDescription,
        jobTitle: job.title || "",
        company: job.company || "",
        location: job.location || "",
        jobType: job.job_type || "",
        experience: job.experience || "",
        jobUrl: job.apply_link || "",
        postedDate: job.posted_date || "",
        source: job.source || "IndianAPI",
      },
    });
  };

  const tailorResume = (job) => {
    const jobDescription = [
      job.description,
      job.responsibilities,
      job.skills,
      job.experience,
      job.about_company,
    ]
      .filter(Boolean)
      .join("\n\n");

    navigate("/resume-builder", {
      state: {
        mode: "modifier",
        resumeId,
        resumeType,
        jobDescription,
        jobTitle: job.title || "",
        company: job.company || "",
        location: job.location || "",
        jobUrl: job.apply_link || "",
      },
    });
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main recommended-jobs-page">
        <div className="recommended-jobs-header">
          <div>
            <div className="recommended-title">
              <Sparkles size={27} />
              <h1>Recommended Jobs</h1>
            </div>

            <p>
              Find real Indian job opportunities matched against your resume
              skills.
            </p>
          </div>

          {searched && (
            <button
              className="refresh-jobs-btn"
              onClick={searchRecommendedJobs}
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "spinning" : ""} />
              Refresh
            </button>
          )}
        </div>

        {error && <div className="recommended-jobs-error">{error}</div>}

        <section className="recommended-search-card">
          <div className="recommended-search-heading">
            <h2>Find Jobs For Your Resume</h2>
            <p>
              We'll compare your demonstrated skills with real job listings.
            </p>
          </div>

          <div className="recommended-search-form">
            <div className="recommended-form-group">
              <label>Resume</label>

              <select
                value={resumeId}
                onChange={handleResumeChange}
                disabled={loadingResumes}
              >
                {resumes.length === 0 ? (
                  <option value="">No resumes available</option>
                ) : (
                  <>
                    {resumes.some((resume) => resume.type === "uploaded") && (
                      <optgroup label="Uploaded Resumes">
                        {resumes
                          .filter((resume) => resume.type === "uploaded")
                          .map((resume) => (
                            <option key={resume.value} value={resume.value}>
                              {resume.label}
                            </option>
                          ))}
                      </optgroup>
                    )}

                    {resumes.some((resume) => resume.type === "generated") && (
                      <optgroup label="Generated Resumes">
                        {resumes
                          .filter((resume) => resume.type === "generated")
                          .map((resume) => (
                            <option key={resume.value} value={resume.value}>
                              {resume.label}
                            </option>
                          ))}
                      </optgroup>
                    )}
                  </>
                )}
              </select>
            </div>

            <div className="recommended-form-group">
              <label>Location</label>

              <input
                type="text"
                value={locationName}
                onChange={(event) => setLocationName(event.target.value)}
                placeholder="e.g. Hyderabad"
              />
            </div>

            <button
              className="find-jobs-btn"
              onClick={searchRecommendedJobs}
              disabled={loading || !resumeId}
            >
              {loading ? (
                <>
                  <Loader2 size={17} className="spinning" />
                  Finding Jobs...
                </>
              ) : (
                <>
                  <Sparkles size={17} />
                  Find Recommended Jobs
                </>
              )}
            </button>
          </div>
        </section>

        {loading && (
          <div className="recommended-jobs-loading">
            <Loader2 size={28} className="spinning" />
            <p>
              Searching real Indian job listings and matching them with your
              resume...
            </p>
          </div>
        )}

        {!loading && searched && jobs.length === 0 && (
          <div className="recommended-jobs-empty">
            <BriefcaseBusiness size={40} />

            <h3>No matching jobs found</h3>

            <p>Try another location or use a different resume.</p>
          </div>
        )}

        {!loading && jobs.length > 0 && (
          <section className="recommended-results">
            <div className="recommended-results-header">
              <div>
                <h2>Jobs Matched To Your Resume</h2>

                <p>{jobs.length} real job opportunities found.</p>
              </div>
            </div>

            <div className="recommended-job-list">
              {jobs.map((job, index) => {
                const match = job.match || {};

                const percentage = Number(match.match_percentage || 0);

                return (
                  <article
                    className="recommended-job-card"
                    key={job.apply_link || job.id || index}
                  >
                    <div className="recommended-job-top">
                      <div className="recommended-company-icon">
                        <BriefcaseBusiness size={21} />
                      </div>

                      <div className="recommended-job-main">
                        <h3>{job.title || "Job Opportunity"}</h3>

                        <p className="recommended-company">
                          {job.company || "Company not specified"}
                        </p>

                        <div className="recommended-job-meta">
                          {job.location && <span>{job.location}</span>}

                          {job.job_type && <span>{job.job_type}</span>}

                          {job.experience && <span>{job.experience}</span>}
                        </div>
                      </div>

                      <div
                        className={`match-score ${getMatchClass(percentage)}`}
                      >
                        <strong>{percentage}%</strong>

                        <span>match</span>
                      </div>
                    </div>

                    <div className="recommended-match-section">
                      {match.matched_skills?.length > 0 && (
                        <div>
                          <span className="match-label">Matching Skills</span>

                          <div className="match-tags">
                            {match.matched_skills.map((skill, skillIndex) => (
                              <span
                                className="match-tag matched"
                                key={skillIndex}
                              >
                                ✓ {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {match.missing_skills?.length > 0 && (
                        <div>
                          <span className="match-label">
                            Job Skills Not Matched
                          </span>

                          <div className="match-tags">
                            {match.missing_skills.map((skill, skillIndex) => (
                              <span
                                className="match-tag missing"
                                key={skillIndex}
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="recommended-job-actions">
                      <button
                        className="recommended-secondary-btn"
                        onClick={() => analyzeJob(job)}
                      >
                        <Sparkles size={16} />
                        Analyze
                      </button>

                      <button
                        className="recommended-secondary-btn"
                        onClick={() => tailorResume(job)}
                      >
                        <FileText size={16} />
                        Tailor Resume
                      </button>

                      {job.apply_link && (
                        <a
                          className="recommended-apply-btn"
                          href={job.apply_link}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink size={16} />
                          Apply
                        </a>
                      )}

                      <button
                        className="recommended-view-btn"
                        onClick={() => analyzeJob(job)}
                      >
                        Details
                        <ArrowRight size={15} />
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default RecommendedJobs;
