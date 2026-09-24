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
  BarChart3,
  Target,
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


  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const navigate = useNavigate();

  const [applications, setApplications] =
    useState([]);

  const [loadingApplications, setLoadingApplications] =
    useState(true);

  const [careerDashboard, setCareerDashboard] =
    useState(null);

  const [loadingCareerDashboard, setLoadingCareerDashboard] =
    useState(true);


  useEffect(() => {

    const fetchApplications = async () => {

      try {

        const response =
          await api.get("/jobs/");

        setApplications(
          response.data
        );

      } catch (err) {

        console.error(
          "Unable to load applications:",
          err
        );

      } finally {

        setLoadingApplications(false);

      }

    };

    fetchApplications();

  }, []);


  useEffect(() => {

    const fetchCareerDashboard = async () => {

      try {

        setLoadingCareerDashboard(true);

        const response =
          await api.get(
            "/career/dashboard/"
          );

        setCareerDashboard(
          response.data
        );

      } catch (err) {

        console.error(
          "Unable to load career dashboard:",
          err
        );

      } finally {

        setLoadingCareerDashboard(false);

      }

    };

    fetchCareerDashboard();

  }, []);


  const applicationStats = {

    total:
      applications.length,

    applied:
      applications.filter(
        (application) =>
          application.status === "applied"
      ).length,

    interviews:
      applications.filter(
        (application) =>
          application.status === "interview"
      ).length,

    offers:
      applications.filter(
        (application) =>
          application.status === "offer"
      ).length,

  };


  const uploadResume = async () => {

    if (!resume) {

      setError(
        "Please select a resume."
      );

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


  const analyzeJob = () => {

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


    setError("");


    navigate(
      "/career-analysis",
      {
        state: {
          resumeId:
            String(resumeId),

          jobDescription:
            jobDescription,
        },
      }
    );

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

              <CheckCircle2
                size={16}
              />

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
>
  <Sparkles size={16} />
  Analyze Job
</button>

        </section>


        {/* Quick Actions */}

        <section className="dashboard-section">

          <div className="section-header">

            <div>

              <h2>
                Quick Actions
              </h2>

              <p>
                Jump directly to your career tools.
              </p>

            </div>

          </div>


          <div className="quick-actions">


            <button
              className="quick-action-card"
              onClick={() =>
                navigate("/resumes")
              }
            >

              <div className="quick-action-icon">

                <FileText size={21} />

              </div>


              <div>

                <h3>
                  Manage Resumes
                </h3>

                <p>
                  Upload and manage your resumes.
                </p>

              </div>


              <ArrowRight size={18} />

            </button>


            <button
              className="quick-action-card"
              onClick={() =>
                navigate("/interview-prep")
              }
            >

              <div className="quick-action-icon">

                <MessageSquare
                  size={21}
                />

              </div>


              <div>

                <h3>
                  Interview Prep
                </h3>

                <p>
                  Generate personalized interview questions.
                </p>

              </div>


              <ArrowRight size={18} />

            </button>


            <button
              className="quick-action-card"
              onClick={() =>
                navigate("/applications")
              }
            >

              <div className="quick-action-icon">

                <Briefcase
                  size={21}
                />

              </div>


              <div>

                <h3>
                  Applications
                </h3>

                <p>
                  Track your job applications.
                </p>

              </div>


              <ArrowRight size={18} />

            </button>

          </div>

        </section>


        {/* Application Overview */}

        <section className="dashboard-section">

          <div className="section-header">

            <div>

              <h2>
                Application Overview
              </h2>

              <p>
                Your current job search activity.
              </p>

            </div>


            <button
              className="view-all-btn"
              onClick={() =>
                navigate("/applications")
              }
            >

              View All

              <ArrowRight size={16} />

            </button>

          </div>


          <div className="dashboard-application-stats">

            <div className="dashboard-stat">

              <span>
                Total Applications
              </span>

              <strong>
                {applicationStats.total}
              </strong>

            </div>


            <div className="dashboard-stat">

              <span>
                Applied
              </span>

              <strong>
                {applicationStats.applied}
              </strong>

            </div>


            <div className="dashboard-stat">

              <span>
                Interviews
              </span>

              <strong>
                {applicationStats.interviews}
              </strong>

            </div>


            <div className="dashboard-stat">

              <span>
                Offers
              </span>

              <strong>
                {applicationStats.offers}
              </strong>

            </div>

          </div>

        </section>


        {/* Career Analysis Overview */}

        <section className="dashboard-section">

          <div className="section-header">

            <div>

              <h2>
                Career Analysis Overview
              </h2>

              <p>
                Your recent AI-powered career analysis activity.
              </p>

            </div>


            <button
              className="view-all-btn"
              onClick={() =>
                navigate("/career-history")
              }
            >

              View History

              <ArrowRight size={16} />

            </button>

          </div>


          {loadingCareerDashboard ? (

            <div className="dashboard-empty-state">

              Loading career analysis...

            </div>

          ) : !careerDashboard ? (

            <div className="dashboard-empty-state">

              <BarChart3 size={30} />

              <h3>
                No career analysis data
              </h3>

              <p>
                Run a career analysis to see your
                career insights here.
              </p>

            </div>

          ) : (

            <>

              <div className="dashboard-application-stats">


                <div className="dashboard-stat">

                  <span>
                    Total Analyses
                  </span>

                  <strong>
                    {
                      careerDashboard.total_analyses ||
                      0
                    }
                  </strong>

                </div>


                <div className="dashboard-stat">

                  <span>
                    Latest Required Skills
                  </span>

                  <strong>
                    {
                      careerDashboard
                        .recent_analyses?.[0]
                        ?.required_skill_count ||
                      0
                    }
                  </strong>

                </div>


                <div className="dashboard-stat">

                  <span>
                    Latest Matching Skills
                  </span>

                  <strong>
                    {
                      careerDashboard
                        .recent_analyses?.[0]
                        ?.matching_skill_count ||
                      0
                    }
                  </strong>

                </div>


                <div className="dashboard-stat">

                  <span>
                    Latest Skill Gaps
                  </span>

                  <strong>
                    {
                      careerDashboard
                        .recent_analyses?.[0]
                        ?.missing_skill_count ||
                      0
                    }
                  </strong>

                </div>

              </div>


              {
                careerDashboard
                  .recent_analyses
                  ?.length > 0 && (

                <div className="recent-applications">

                  {
                    careerDashboard
                      .recent_analyses
                      .map(
                        (analysis) => (

                          <div
                            className="recent-application"
                            key={analysis.id}
                          >

                            <div className="recent-application-icon">

                              <Target size={18} />

                            </div>


                            <div className="recent-application-info">

                              <h3>

                                {
                                  analysis.resume_title ||
                                  "Career Analysis"
                                }

                              </h3>


                              <p>

                                Matching:{" "}

                                {
                                  analysis.matching_skill_count
                                }

                                {" · "}

                                Missing:{" "}

                                {
                                  analysis.missing_skill_count
                                }

                              </p>

                            </div>


                            <button
                              className="view-all-btn"
                              onClick={() =>
                                navigate(
                                  `/career-history/${analysis.id}`
                                )
                              }
                            >

                              View

                              <ArrowRight
                                size={15}
                              />

                            </button>

                          </div>

                        )
                      )
                  }

                </div>

              )}

            </>

          )}

        </section>


        {error && (

          <p className="error-message">

            {error}

          </p>

        )}



        {/* Recent Applications */}

        <section className="dashboard-section">

          <div className="section-header">

            <div>

              <h2>
                Recent Applications
              </h2>

              <p>
                Your latest tracked opportunities.
              </p>

            </div>


            <button
              className="view-all-btn"
              onClick={() =>
                navigate("/applications")
              }
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

              <h3>
                No applications yet
              </h3>

              <p>
                Start tracking your job applications from the
                Applications page.
              </p>


              <button
                className="dashboard-primary-btn"
                onClick={() =>
                  navigate("/applications")
                }
              >

                <Plus size={17} />

                Add Application

              </button>

            </div>

          ) : (

            <div className="recent-applications">

              {
                applications
                  .slice(0, 5)
                  .map(
                    (application) => (

                      <div
                        className="recent-application"
                        key={application.id}
                      >

                        <div className="recent-application-icon">

                          <Briefcase
                            size={18}
                          />

                        </div>


                        <div className="recent-application-info">

                          <h3>
                            {application.job_title}
                          </h3>

                          <p>
                            {application.company}
                          </p>

                        </div>


                        <span
                          className={`dashboard-status status-${application.status}`}
                        >
                          {application.status}
                        </span>

                      </div>

                    )
                  )
              }

            </div>

          )}

        </section>


      </main>

    </div>

  );

}



export default Dashboard;