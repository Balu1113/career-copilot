import { useEffect, useState } from "react";
import {
  BookOpen,
  Briefcase,
  CheckCircle2,
  MessageSquare,
  Sparkles,
  Target,
} from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./InterviewPrep.css";

function InterviewPrep() {
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);

  const [loadingResumes, setLoadingResumes] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchResumes = async () => {
      try {
        const response = await api.get("/resumes/");

        setResumes(response.data);

        if (response.data.length > 0) {
          setResumeId(String(response.data[0].id));
        }
      } catch (err) {
        setError("Unable to load your resumes.");
      } finally {
        setLoadingResumes(false);
      }
    };

    fetchResumes();
  }, []);

  const generatePreparation = async (event) => {
    event.preventDefault();

    if (!resumeId) {
      setError("Please select a resume.");
      return;
    }

    if (jobDescription.trim().length < 50) {
      setError(
        "Please enter a job description with at least 50 characters."
      );
      return;
    }

    try {
      setGenerating(true);
      setError("");
      setResult(null);

      const response = await api.post(
        "/career/interview-prep/",
        {
          resume_id: Number(resumeId),
          job_description: jobDescription,
        }
      );

      setResult(response.data.interview_preparation);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.detail ||
          "Unable to generate interview preparation."
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main interview-page">
        <div className="interview-header">
          <div>
            <div className="page-title-row">
              <Sparkles size={25} />
              <h1>Interview Preparation</h1>
            </div>

            <p>
              Get personalized interview questions and
              preparation based on your resume and target role.
            </p>
          </div>
        </div>

        {error && (
          <div className="interview-error">
            {error}
          </div>
        )}

        <section className="interview-input-card">
          <div className="section-heading">
            <div className="section-icon">
              <Target size={20} />
            </div>

            <div>
              <h2>Prepare for your interview</h2>
              <p>
                Select your resume and paste the target job
                description.
              </p>
            </div>
          </div>

          <form onSubmit={generatePreparation}>
            <div className="form-group">
              <label>Select Resume</label>

              {loadingResumes ? (
                <div className="loading-text">
                  Loading resumes...
                </div>
              ) : resumes.length === 0 ? (
                <div className="no-resume-message">
                  No resumes found. Please upload a resume first.
                </div>
              ) : (
                <select
                  value={resumeId}
                  onChange={(event) =>
                    setResumeId(event.target.value)
                  }
                >
                  {resumes.map((resume) => (
                    <option
                      key={resume.id}
                      value={resume.id}
                    >
                      {resume.title}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group">
              <label>Job Description</label>

              <textarea
                value={jobDescription}
                onChange={(event) =>
                  setJobDescription(event.target.value)
                }
                placeholder="Paste the job description here..."
                rows="10"
              />

              <div className="character-count">
                {jobDescription.length} characters
              </div>
            </div>

            <button
              type="submit"
              className="generate-interview-btn"
              disabled={
                generating ||
                loadingResumes ||
                resumes.length === 0
              }
            >
              <Sparkles size={18} />

              {generating
                ? "Generating..."
                : "Generate Interview Prep"}
            </button>
          </form>
        </section>

        {generating && (
          <div className="generation-loader">
            <div className="loader-spinner"></div>

            <h3>Analyzing your profile...</h3>

            <p>
              Comparing your resume with the job requirements
              and generating personalized questions.
            </p>
          </div>
        )}

        {result && !generating && (
          <div className="interview-results">
            <div className="results-heading">
              <div>
                <h2>Your Interview Preparation</h2>
                <p>
                  Personalized preparation generated from your
                  resume and target role.
                </p>
              </div>

              <CheckCircle2 size={28} />
            </div>

            <InterviewSection
              icon={<BookOpen size={20} />}
              title="Technical Questions"
              items={result.technical_questions}
              renderItem={(item) => (
                <>
                  <h3>{item.question}</h3>

                  {item.why_asked && (
                    <p>
                      <strong>Why:</strong>{" "}
                      {item.why_asked}
                    </p>
                  )}

                  {item.preparation_hint && (
                    <p>
                      <strong>Prepare:</strong>{" "}
                      {item.preparation_hint}
                    </p>
                  )}
                </>
              )}
            />

            <InterviewSection
              icon={<Briefcase size={20} />}
              title="Resume-Based Questions"
              items={result.resume_questions}
              renderItem={(item) => (
                <>
                  <h3>{item.question}</h3>

                  {item.focus_area && (
                    <p>
                      <strong>Focus:</strong>{" "}
                      {item.focus_area}
                    </p>
                  )}
                </>
              )}
            />

            <InterviewSection
              icon={<Target size={20} />}
              title="Project Questions"
              items={result.project_questions}
              renderItem={(item) => (
                <>
                  <h3>{item.question}</h3>

                  {item.focus_area && (
                    <p>
                      <strong>Focus:</strong>{" "}
                      {item.focus_area}
                    </p>
                  )}
                </>
              )}
            />

            <InterviewSection
              icon={<MessageSquare size={20} />}
              title="HR Questions"
              items={result.hr_questions}
              renderItem={(item) => (
                <>
                  <h3>{item.question}</h3>

                  {item.preparation_hint && (
                    <p>
                      <strong>Prepare:</strong>{" "}
                      {item.preparation_hint}
                    </p>
                  )}
                </>
              )}
            />

            <div className="result-grid">
              <div className="result-list-card">
                <div className="result-card-heading">
                  <BookOpen size={19} />
                  <h2>Topics to Revise</h2>
                </div>

                <ul>
                  {(result.topics_to_revise || []).map(
                    (topic, index) => (
                      <li key={index}>
                        <CheckCircle2 size={16} />
                        {topic}
                      </li>
                    )
                  )}
                </ul>
              </div>

              <div className="result-list-card">
                <div className="result-card-heading">
                  <Target size={19} />
                  <h2>Preparation Strategy</h2>
                </div>

                <ol>
                  {(result.preparation_strategy || []).map(
                    (step, index) => (
                      <li key={index}>{step}</li>
                    )
                  )}
                </ol>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function InterviewSection({
  icon,
  title,
  items,
  renderItem,
}) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <section className="interview-result-section">
      <div className="result-section-title">
        <div className="result-section-icon">
          {icon}
        </div>

        <h2>{title}</h2>
      </div>

      <div className="question-list">
        {items.map((item, index) => (
          <div className="question-card" key={index}>
            <div className="question-number">
              {index + 1}
            </div>

            <div className="question-content">
              {renderItem(item)}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default InterviewPrep;