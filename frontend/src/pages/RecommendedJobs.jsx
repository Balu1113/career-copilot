import { useEffect, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  ExternalLink,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
  X,
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

  const [preparingJobId, setPreparingJobId] = useState(null);
  const [applicationPackage, setApplicationPackage] = useState(null);
  const [applicationError, setApplicationError] = useState("");

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
        console.error("Failed to load resumes:", err);
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

  const buildJobDescription = (job) => {
    return [
      job.description,
      job.responsibilities,
      job.skills,
      job.experience,
      job.about_company,
    ]
      .filter(Boolean)
      .join("\n\n");
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
      console.error("Failed to load recommended jobs:", err);

      setError(
        err.response?.data?.detail || "Unable to load recommended jobs.",
      );

      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAndTrack = async () => {
    if (!applicationPackage?.job) {
      return;
    }

    try {
      setApplicationError("");

      const job = applicationPackage.job;

      const response = await api.post("/jobs/approve-application/", {
        company: job.company || "",
        job_title: job.title || "",
        job_url: job.apply_link || "",
        notes:
          "Prepared using AI Application Agent. User reviewed the application package before tracking.",
      });

      setApplicationPackage(null);

      navigate("/applications", {
        state: {
          applicationCreated: true,
          application: response.data,
        },
      });
    } catch (err) {
      console.error("Failed to track application:", err);

      setApplicationError(
        err.response?.data?.detail || "Unable to track the application.",
      );
    }
  };

  const analyzeJob = (job) => {
    const jobDescription = buildJobDescription(job);

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

  const tailorResume = (job, optimization = null) => {
    const jobDescription = buildJobDescription(job);

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
        optimization,
      },
    });
  };

  const handlePrepareApplication = async (job) => {
    if (!resumeId) {
      setApplicationError(
        "Please select a resume before preparing an application.",
      );
      return;
    }

    const [, selectedId] = String(resumeId).split(":");

    if (!selectedId) {
      setApplicationError("Invalid resume selection.");
      return;
    }

    try {
      setPreparingJobId(job.id);
      setApplicationError("");
      setApplicationPackage(null);

      const response = await api.post("/agents/application-agent/", {
        job,
        resume: {
          id: selectedId,
          type: resumeType || "uploaded",
        },
      });

      setApplicationPackage({
        job,
        ...response.data,
      });
    } catch (err) {
      console.error("Application agent failed:", err);

      setApplicationError(
        err.response?.data?.detail || "Unable to prepare the application.",
      );
    } finally {
      setPreparingJobId(null);
    }
  };

  const closeApplicationReview = () => {
    setApplicationPackage(null);
    setApplicationError("");
  };

  const handleTailorFromApplication = () => {
    if (!applicationPackage?.job) {
      return;
    }

    tailorResume(
      applicationPackage.job,
      applicationPackage.optimization || null,
    );
  };

  const handleReviewAndApply = () => {
    const url =
      applicationPackage?.job?.apply_link || applicationPackage?.job?.job_url;

    if (!url) {
      setApplicationError("This job does not have an application URL.");
      return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
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

        {applicationError && (
          <div className="recommended-jobs-error">{applicationError}</div>
        )}

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

                <p>
                  {jobs.length} real job
                  {jobs.length !== 1 ? " opportunities" : " opportunity"} found.
                </p>
              </div>
            </div>

            <div className="recommended-job-list">
              {jobs.map((job, index) => {
                const match = job.match || {};

                const percentage = Number(match.match_percentage || 0);

                const jobKey = job.apply_link || job.id || index;

                const isPreparing = preparingJobId === job.id;

                return (
                  <article className="recommended-job-card" key={jobKey}>
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

                      <button
                        className="prepare-application-btn"
                        onClick={() => handlePrepareApplication(job)}
                        disabled={isPreparing}
                      >
                        {isPreparing ? (
                          <>
                            <Loader2 size={16} className="spinning" />
                            Preparing...
                          </>
                        ) : (
                          <>
                            <Sparkles size={16} />
                            Prepare Application
                          </>
                        )}
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

        {/* Human Review Modal */}
        {applicationPackage && (
          <div className="application-agent-modal-overlay">
            <div className="application-agent-modal">
              <div className="application-agent-header">
                <div>
                  <span className="application-agent-badge">
                    AI Application Agent
                  </span>

                  <h2>Review Your Application</h2>

                  <p>
                    The agent prepared this application package. Review the
                    details before applying.
                  </p>
                </div>

                <button
                  className="application-agent-close"
                  onClick={closeApplicationReview}
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="application-agent-content">
                <div className="application-review-section">
                  <h3>Job</h3>

                  <p>
                    <strong>
                      {applicationPackage.job?.title || "Job Opportunity"}
                    </strong>
                  </p>

                  <p>
                    {applicationPackage.job?.company || "Company not specified"}
                  </p>

                  {applicationPackage.job?.location && (
                    <p>{applicationPackage.job.location}</p>
                  )}
                </div>

                {applicationPackage.application_data && (
                  <div className="application-review-section">
                    <h3>Application Data</h3>

                    <div className="application-review-grid">
                      <div>
                        <span>Job Title</span>

                        <strong>
                          {applicationPackage.application_data.job_title}
                        </strong>
                      </div>

                      <div>
                        <span>Company</span>

                        <strong>
                          {applicationPackage.application_data.company}
                        </strong>
                      </div>

                      <div>
                        <span>Resume Type</span>

                        <strong>
                          {applicationPackage.application_data.resume_type}
                        </strong>
                      </div>
                    </div>
                  </div>
                )}

                {applicationPackage.optimization?.optimization_summary && (
                  <div className="application-review-section">
                    <h3>Resume Optimization</h3>

                    <p>
                      {applicationPackage.optimization.optimization_summary}
                    </p>
                  </div>
                )}

                {applicationPackage.optimization?.safe_ats_keywords?.length >
                  0 && (
                  <div className="application-review-section">
                    <h3>Safe ATS Keywords</h3>

                    <div className="application-agent-tags">
                      {applicationPackage.optimization.safe_ats_keywords.map(
                        (keyword, index) => (
                          <span key={index}>{keyword}</span>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {applicationPackage.optimization?.missing_requirements?.length >
                  0 && (
                  <div className="application-review-section">
                    <h3>Missing Requirements</h3>

                    <div className="application-agent-tags missing">
                      {applicationPackage.optimization.missing_requirements.map(
                        (requirement, index) => (
                          <span key={index}>{requirement}</span>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {applicationPackage.optimization?.bullet_suggestions?.length >
                  0 && (
                  <div className="application-review-section">
                    <h3>Resume Improvements</h3>

                    <div className="application-agent-suggestions">
                      {applicationPackage.optimization.bullet_suggestions.map(
                        (suggestion, index) => (
                          <div
                            className="application-agent-suggestion"
                            key={index}
                          >
                            <span>{suggestion.section || "Resume"}</span>

                            <p>
                              <strong>Current:</strong> {suggestion.original}
                            </p>

                            <p>
                              <strong>Suggested:</strong> {suggestion.improved}
                            </p>

                            {suggestion.reason && (
                              <small>{suggestion.reason}</small>
                            )}
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}

                <div className="application-agent-approval">
                  <strong>🔒 Human approval required</strong>

                  <p>
                    Nothing is submitted automatically. Review the application
                    and explicitly choose whether to continue.
                  </p>
                </div>
              </div>

              <div className="application-agent-actions">
                <button
                  className="application-agent-approve"
                  onClick={handleApproveAndTrack}
                >
                  <CheckCircle2 size={16} />
                  Approve & Track Application
                </button>
                <button
                  className="application-agent-cancel"
                  onClick={closeApplicationReview}
                >
                  Close
                </button>

                <button
                  className="application-agent-tailor"
                  onClick={handleTailorFromApplication}
                >
                  <FileText size={16} />
                  Tailor Resume
                </button>

                <button
                  className="application-agent-apply"
                  onClick={handleReviewAndApply}
                >
                  <ExternalLink size={16} />
                  Review & Apply
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default RecommendedJobs;
