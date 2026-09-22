import { useState, useEffect } from "react";
import {
  ArrowRight,
  Briefcase,
  CheckCircle2,
  FileText,
  LoaderCircle,
  MessageSquare,
  Plus,
  Sparkles,
  Upload,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./Dashboard.css";


function Dashboard() {

  const [resume, setResume] = useState(null);

  const [resumeId, setResumeId] =
    useState(null);

  const [jobDescription, setJobDescription] =
    useState("");

  const [analysis, setAnalysis] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const navigate = useNavigate();

  const [applications, setApplications] = useState([]);
  const [loadingApplications, setLoadingApplications] = useState(true);

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const response = await api.get("/jobs/");
        setApplications(response.data);
      } catch (err) {
        console.error("Unable to load applications:", err);
      } finally {
        setLoadingApplications(false);
      }
    };

    fetchApplications();
  }, []);

  const applicationStats = {
    total: applications.length,

    applied: applications.filter(
      (application) => application.status === "applied"
    ).length,

    interviews: applications.filter(
      (application) => application.status === "interview"
    ).length,

    offers: applications.filter(
      (application) => application.status === "offer"
    ).length,
  };


  const uploadResume = async () => {

    if (!resume) {
      setError("Please select a resume.");
      return;
    }

    try {

      setError("");
      setUploading(true);

      const formData =
        new FormData();

      formData.append(
        "title",
        resume.name
      );

      formData.append(
        "file",
        resume
      );


      const response =
        await api.post(
          "/resumes/",
          formData
        );


      setResumeId(
        response.data.id
      );

    } catch (error) {

      setError(
        error.response?.data?.error ||
        "Resume upload failed."
      );

    } finally {

      setUploading(false);
    }
  };


  const analyzeJob = async () => {

    if (!resumeId) {
      setError(
        "Please upload your resume first."
      );
      return;
    }


    if (!jobDescription.trim()) {
      setError(
        "Please enter a job description."
      );
      return;
    }


    try {

      setError("");
      setAnalysis(null);
      setLoading(true);


      const response =
        await api.post(
          "/career/analyze/",
          {
            resume_id: resumeId,
            job_description:
              jobDescription,
          }
        );


      setAnalysis(
        response.data
      );

    } catch (error) {

      setError(
        error.response?.data?.error ||
        "Career analysis failed."
      );

    } finally {

      setLoading(false);
    }
  };


  return (
    <div className="dashboard-layout">

      <Sidebar />


      <main className="dashboard-main">

        <header className="dashboard-header">

          <h1>
            AI Career Copilot
          </h1>

          <p>
            Analyze your resume and discover
            how you match your target role.
          </p>

        </header>


        {/* Resume */}

        <section className="card">

          <h2>
            Your Resume
          </h2>

          <p className="card-description">
            Upload your latest resume to
            power the AI analysis.
          </p>


          <div className="upload-area">

            <Upload
              className="upload-icon"
              size={32}
            />

            <p>
              Select your resume
            </p>

            <p className="file-types">
              PDF or DOCX
            </p>


            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(event) =>
                setResume(
                  event.target.files[0]
                )
              }
            />


            {resume && (
              <p className="file-name">
                <FileText size={16} />
                {" "}
                {resume.name}
              </p>
            )}

          </div>


          <button
            className="primary-button"
            onClick={uploadResume}
            disabled={uploading}
          >

            {uploading ? (
              <>
                <LoaderCircle
                  size={16}
                  className="spin"
                />
                Uploading...
              </>
            ) : (
              "Upload Resume"
            )}

          </button>


          {resumeId && (
            <p className="success-message">

              <CheckCircle2 size={16} />

              {" "}
              Resume uploaded successfully.

            </p>
          )}

        </section>


        {/* Job */}

        <section className="card">

          <h2>
            Target Job
          </h2>

          <p className="card-description">
            Paste the job description you
            want to analyze.
          </p>


          <textarea
            className="job-textarea"
            placeholder="Paste the complete job description here..."
            value={jobDescription}
            onChange={(event) =>
              setJobDescription(
                event.target.value
              )
            }
          />


          <button
            className="primary-button"
            onClick={analyzeJob}
            disabled={loading}
          >

            {loading ? (
              <>
                <LoaderCircle
                  size={16}
                  className="spin"
                />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Analyze Job
              </>
            )}

          </button>

        </section>


        {/* Quick Actions */}

        <section className="dashboard-section">
          <div className="section-header">
            <div>
              <h2>Quick Actions</h2>
              <p>Jump directly to your career tools.</p>
            </div>
          </div>

          <div className="quick-actions">
            <button
              className="quick-action-card"
              onClick={() => navigate("/resumes")}
            >
              <div className="quick-action-icon">
                <FileText size={21} />
              </div>

              <div>
                <h3>Manage Resumes</h3>
                <p>Upload and manage your resumes.</p>
              </div>

              <ArrowRight size={18} />
            </button>

            <button
              className="quick-action-card"
              onClick={() => navigate("/interview-prep")}
            >
              <div className="quick-action-icon">
                <MessageSquare size={21} />
              </div>

              <div>
                <h3>Interview Prep</h3>
                <p>Generate personalized interview questions.</p>
              </div>

              <ArrowRight size={18} />
            </button>

            <button
              className="quick-action-card"
              onClick={() => navigate("/applications")}
            >
              <div className="quick-action-icon">
                <Briefcase size={21} />
              </div>

              <div>
                <h3>Applications</h3>
                <p>Track your job applications.</p>
              </div>

              <ArrowRight size={18} />
            </button>
          </div>
        </section>


        {/* Application Overview */}

        <section className="dashboard-section">
          <div className="section-header">
            <div>
              <h2>Application Overview</h2>
              <p>Your current job search activity.</p>
            </div>

            <button
              className="view-all-btn"
              onClick={() => navigate("/applications")}
            >
              View All
              <ArrowRight size={16} />
            </button>
          </div>

          <div className="dashboard-application-stats">
            <div className="dashboard-stat">
              <span>Total Applications</span>
              <strong>{applicationStats.total}</strong>
            </div>

            <div className="dashboard-stat">
              <span>Applied</span>
              <strong>{applicationStats.applied}</strong>
            </div>

            <div className="dashboard-stat">
              <span>Interviews</span>
              <strong>{applicationStats.interviews}</strong>
            </div>

            <div className="dashboard-stat">
              <span>Offers</span>
              <strong>{applicationStats.offers}</strong>
            </div>
          </div>
        </section>


        {error && (
          <p className="error-message">
            {error}
          </p>
        )}


        {/* Results */}

        {analysis && (

          <section>

            <div className="results-header">

              <Sparkles size={22} />

              <h2>
                AI Career Analysis
              </h2>

            </div>


            <div className="results-grid">


              <div className="result-card">

                <h3>
                  Job Requirements
                </h3>

                <ResultList
                  items={
                    analysis
                      .job_requirements
                      ?.required_skills
                  }
                />

              </div>


              <div className="result-card">

                <h3>
                  Matching Skills
                </h3>

                <ResultList
                  items={
                    analysis
                      .resume_analysis
                      ?.matching_skills
                  }
                />

              </div>


              <div className="result-card">

                <h3>
                  Skill Gaps
                </h3>

                <ResultList
                  items={
                    analysis
                      .skill_gap_analysis
                      ?.missing_skills
                  }
                />

              </div>


              <div className="result-card">

                <h3>
                  Recommended Topics
                </h3>

                <ResultList
                  items={
                    analysis
                      .career_recommendation
                      ?.recommended_topics
                  }
                />

              </div>


            </div>


            <div className="result-card">

              <h3>
                Career Recommendations
              </h3>

              <ResultList
                items={
                  analysis
                    .career_recommendation
                    ?.next_steps
                }
              />

            </div>

          </section>

        )}


        {/* Recent Applications */}

        <section className="dashboard-section">
          <div className="section-header">
            <div>
              <h2>Recent Applications</h2>
              <p>Your latest tracked opportunities.</p>
            </div>

            <button
              className="view-all-btn"
              onClick={() => navigate("/applications")}
            >
              View All
              <ArrowRight size={16} />
            </button>
          </div>

          {loadingApplications ? (
            <div className="dashboard-empty-state">
              Loading applications...
            </div>
          ) : applications.length === 0 ? (
            <div className="dashboard-empty-state">
              <Briefcase size={30} />

              <h3>No applications yet</h3>

              <p>
                Start tracking your job applications from the
                Applications page.
              </p>

              <button
                className="dashboard-primary-btn"
                onClick={() => navigate("/applications")}
              >
                <Plus size={17} />
                Add Application
              </button>
            </div>
          ) : (
            <div className="recent-applications">
              {applications.slice(0, 5).map((application) => (
                <div
                  className="recent-application"
                  key={application.id}
                >
                  <div className="recent-application-icon">
                    <Briefcase size={18} />
                  </div>

                  <div className="recent-application-info">
                    <h3>{application.job_title}</h3>
                    <p>{application.company}</p>
                  </div>

                  <span
                    className={`dashboard-status status-${application.status}`}
                  >
                    {application.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

      </main>

    </div>
  );
}


function ResultList({ items }) {

  if (!items?.length) {

    return (
      <p className="result-summary">
        No information available.
      </p>
    );
  }


  return (
    <ul className="result-list">

      {items.map(
        (item, index) => (
          <li key={index}>
            {item}
          </li>
        )
      )}

    </ul>
  );
}


export default Dashboard;