import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Loader2,
  MessageSquare,
  Play,
  RotateCcw,
  Target,
  Trophy,
  XCircle,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import api from "../services/api";
import "./InterviewSimulator.css";

const INTERVIEW_TYPES = [
  { value: "mixed", label: "Mixed" },
  { value: "technical", label: "Technical" },
  { value: "project", label: "Project" },
  { value: "gap_based", label: "Gap Based" },
  { value: "behavioral", label: "Behavioral" },
];

function InterviewSimulator() {
  const navigate = useNavigate();
  const location = useLocation();
  const resumeSessionId =
    location.state?.sessionId || null;

  const [analyses, setAnalyses] = useState([]);

  const [analysisId, setAnalysisId] = useState(
    location.state?.analysisId || "",
  );

  const [targetRole, setTargetRole] = useState(
    location.state?.targetRole || "",
  );

  const [interviewType, setInterviewType] = useState("mixed");

  const [session, setSession] = useState(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState(null);

  const [loadingAnalyses, setLoadingAnalyses] = useState(true);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const loadAnalyses = useCallback(async () => {
    try {
      setError("");

      const response = await api.get("/career/history/");

      const data = response.data || [];

      setAnalyses(data);
      setAnalysisId(
        (current) => current || data[0]?.id || "",
      );
      setTargetRole(
        (current) =>
          current ||
          data[0]?.target_role ||
          data[0]?.job_title ||
          "",
      );
    } catch (err) {
      console.error(
        "Failed to load career analyses:",
        err,
      );

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to load career analyses.",
      );
    }
  }, []);

  const loadResumableSession = useCallback(
    async (sessionId) => {
      try {
        setError("");
        setAnswer("");
        setEvaluation(null);

        const response = await api.get(
          `/career/interview/sessions/${sessionId}/`,
        );
        const resumedSession = response.data;

        setAnalysisId(
          resumedSession.career_analysis_id || "",
        );
        setTargetRole(resumedSession.target_role || "");
        setSession(resumedSession);
      } catch (err) {
        console.error(
          "Failed to resume interview:",
          err,
        );

        setError(
          err.response?.data?.detail ||
            err.response?.data?.error ||
            "Unable to continue this interview.",
        );
      }
    },
    [],
  );

  useEffect(() => {
    const timeoutId = window.setTimeout(async () => {
      setLoadingAnalyses(true);

      const requests = [loadAnalyses()];

      if (resumeSessionId) {
        requests.push(
          loadResumableSession(resumeSessionId),
        );
      }

      await Promise.all(requests);
      setLoadingAnalyses(false);
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [
    loadAnalyses,
    loadResumableSession,
    resumeSessionId,
  ]);

  const handleStartInterview = async () => {
    if (!analysisId) {
      setError(
        "Please select a career analysis first.",
      );
      return;
    }

    try {
      setStarting(true);
      setError("");
      setEvaluation(null);
      setAnswer("");

      const response = await api.post(
        "/career/interview/start/",
        {
          analysis_id: analysisId,
          target_role: targetRole,
          interview_type: interviewType,
        },
      );

      setSession(response.data);
    } catch (err) {
      console.error(
        "Failed to start interview:",
        err,
      );

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to start the interview.",
      );
    } finally {
      setStarting(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!session?.session_id) {
      return;
    }

    if (!answer.trim()) {
      setError("Please enter your answer first.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      const response = await api.post(
        "/career/interview/answer/",
        {
          session_id: session.session_id,
          answer: answer.trim(),
        },
      );

      setEvaluation(response.data.evaluation);

      setSession((previous) => ({
        ...previous,
        completed: response.data.completed,
        overall_score:
          response.data.overall_score,
        current_question_index:
          response.data.next_question_index ??
          previous.current_question_index,
        question: response.data.next_question,
      }));

      setAnswer("");
    } catch (err) {
      console.error(
        "Failed to submit interview answer:",
        err,
      );

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to evaluate your answer.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRestart = () => {
    setSession(null);
    setEvaluation(null);
    setAnswer("");
    setError("");
  };

  const currentQuestion =
    session?.question || null;

  const questionNumber =
    session &&
    session.current_question_index !== null
      ? session.current_question_index + 1
      : 1;

  const totalQuestions =
    session?.total_questions || 0;

  const interviewCompleted =
    session?.completed === true;

  /*
   * Loading State
   */
  if (loadingAnalyses) {
    return (
      <div className="app-layout">
        <Sidebar />

        <main className="main-content">
          <div className="interview-simulator-page">
            <div className="interview-loading">
              <Loader2
                size={28}
                className="interview-spin"
              />

              <p>
                Loading your career analyses...
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="interview-simulator-page">

          {/* Header */}
          <div className="interview-simulator-header">
            <button
              className="interview-back-button"
              onClick={() => navigate("/dashboard")}
            >
              <ArrowLeft size={17} />
              Dashboard
            </button>

            <div className="interview-title-row">
              <div className="interview-title-icon">
                <MessageSquare size={23} />
              </div>

              <div>
                <h1>Interview Simulator</h1>

                <p>
                  Practice role-specific interview
                  questions and receive AI-powered
                  feedback.
                </p>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="interview-error">
              <XCircle size={17} />

              <span>{error}</span>
            </div>
          )}

          {/* =====================================================
              SETUP
          ===================================================== */}

          {!session ? (
            <div className="interview-setup-card">

              <div className="interview-setup-header">
                <div>
                  <span className="interview-eyebrow">
                    AI Interview Practice
                  </span>

                  <h2>
                    Prepare for your next interview
                  </h2>

                  <p>
                    Questions are generated from your
                    existing career analysis and resume
                    evidence.
                  </p>
                </div>

                <div className="interview-setup-icon">
                  <Target size={27} />
                </div>
              </div>

              <div className="interview-form">

                {/* Career Analysis */}
                <div className="interview-field">
                  <label>
                    Career Analysis
                  </label>

                  <select
                    value={analysisId}
                    onChange={(event) => {
                      const value =
                        event.target.value;

                      setAnalysisId(value);

                      const selected =
                        analyses.find(
                          (item) =>
                            String(item.id) ===
                            String(value),
                        );

                      if (selected) {
                        setTargetRole(
                          selected.target_role ||
                            selected.job_title ||
                            "",
                        );
                      }
                    }}
                  >
                    <option value="">
                      Select a career analysis
                    </option>

                    {analyses.map((analysis) => (
                      <option
                        key={analysis.id}
                        value={analysis.id}
                      >
                        {analysis.resume_title ||
                          `Career Analysis #${analysis.id}`}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target Role */}
                <div className="interview-field">
                  <label>
                    Target Role
                  </label>

                  <input
                    type="text"
                    value={targetRole}
                    onChange={(event) =>
                      setTargetRole(
                        event.target.value,
                      )
                    }
                    placeholder="e.g. AI Engineer"
                  />
                </div>

                {/* Interview Type */}
                <div className="interview-field">
                  <label>
                    Interview Type
                  </label>

                  <div className="interview-type-grid">
                    {INTERVIEW_TYPES.map((type) => (
                      <button
                        key={type.value}
                        type="button"
                        className={`interview-type-option ${
                          interviewType ===
                          type.value
                            ? "active"
                            : ""
                        }`}
                        onClick={() =>
                          setInterviewType(
                            type.value,
                          )
                        }
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>

              </div>

              {/* Start */}
              <button
                className="start-interview-button"
                onClick={handleStartInterview}
                disabled={
                  starting || !analysisId
                }
              >
                {starting ? (
                  <>
                    <Loader2
                      size={17}
                      className="interview-spin"
                    />

                    Starting Interview...
                  </>
                ) : (
                  <>
                    <Play size={17} />

                    Start Interview
                  </>
                )}
              </button>
            </div>

          ) : interviewCompleted ? (

            /* =================================================
               COMPLETED
            ================================================= */

            <div className="interview-completed-card">

              <div className="interview-completed-icon">
                <Trophy size={34} />
              </div>

              <span className="interview-eyebrow">
                Interview Completed
              </span>

              <h2>
                Your Interview Score
              </h2>

              <div className="interview-final-score">
                {session.overall_score ?? 0}

                <span>/100</span>
              </div>

              {evaluation && (
                <div className="final-evaluation-preview">
                  <h3>
                    Last Answer Feedback
                  </h3>

                  <p>
                    Your final answer was evaluated
                    using the same AI evaluator used
                    throughout the interview.
                  </p>
                </div>
              )}

              <div className="completed-actions">

                <button
                  className="secondary-interview-button"
                  onClick={handleRestart}
                >
                  <RotateCcw size={17} />

                  Start Another Interview
                </button>

                <button
                  className="primary-interview-button"
                  onClick={() =>
                    navigate("/career-history")
                  }
                >
                  View Career History

                  <ChevronRight size={17} />
                </button>

              </div>
            </div>

          ) : (

            /* =================================================
               ACTIVE INTERVIEW
            ================================================= */

            <div className="interview-session">

              {/* Progress */}
              <div className="interview-progress-card">

                <div>
                  <span>
                    Question {questionNumber}

                    {totalQuestions
                      ? ` of ${totalQuestions}`
                      : ""}
                  </span>

                  <strong>
                    {session.target_role}
                  </strong>
                </div>

                <div className="interview-progress-track">
                  <div
                    className="interview-progress-fill"
                    style={{
                      width: totalQuestions
                        ? `${
                            (questionNumber /
                              totalQuestions) *
                            100
                          }%`
                        : "0%",
                    }}
                  />
                </div>
              </div>

              {/* Question */}
              <div className="interview-question-card">

                <div className="question-meta">

                  <span>
                    {currentQuestion?.category ||
                      "General"}
                  </span>

                  <span>
                    {currentQuestion?.difficulty ||
                      "Medium"}
                  </span>

                </div>

                <h2>
                  {currentQuestion?.question}
                </h2>

                {currentQuestion?.reason && (
                  <p className="question-reason">
                    <strong>
                      Why this question:
                    </strong>{" "}
                    {currentQuestion.reason}
                  </p>
                )}

                {/* Answer */}
                <div className="answer-section">

                  <label htmlFor="interview-answer">
                    Your Answer
                  </label>

                  <textarea
                    id="interview-answer"
                    value={answer}
                    onChange={(event) =>
                      setAnswer(event.target.value)
                    }
                    placeholder="Explain your answer clearly. Include relevant examples from your experience where appropriate..."
                    rows={9}
                    disabled={submitting}
                  />

                  <div className="answer-footer">

                    <span>
                      {answer.trim().length}{" "}
                      characters
                    </span>

                    <button
                      className="submit-answer-button"
                      onClick={
                        handleSubmitAnswer
                      }
                      disabled={
                        submitting ||
                        !answer.trim()
                      }
                    >
                      {submitting ? (
                        <>
                          <Loader2
                            size={17}
                            className="interview-spin"
                          />

                          Evaluating...
                        </>
                      ) : (
                        <>
                          Submit Answer

                          <ChevronRight
                            size={17}
                          />
                        </>
                      )}
                    </button>

                  </div>
                </div>
              </div>

              {/* Evaluation */}
              {evaluation && (
                <div className="interview-evaluation-card">

                  <div className="evaluation-header">

                    <div>
                      <span className="interview-eyebrow">
                        AI Evaluation
                      </span>

                      <h2>
                        Answer Feedback
                      </h2>
                    </div>

                    <div className="evaluation-score">
                      {evaluation.score}

                      <span>/100</span>
                    </div>

                  </div>

                  <div className="evaluation-grid">

                    {/* Strengths */}
                    <div className="evaluation-section">
                      <h3>
                        <CheckCircle2 size={17} />
                        Strengths
                      </h3>

                      <ul>
                        {evaluation.strengths?.map(
                          (item, index) => (
                            <li key={index}>
                              {item}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                    {/* Missing Points */}
                    <div className="evaluation-section">
                      <h3>
                        <Target size={17} />
                        Missing Points
                      </h3>

                      <ul>
                        {evaluation.missing_points?.map(
                          (item, index) => (
                            <li key={index}>
                              {item}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                    {/* Improvements */}
                    <div className="evaluation-section">
                      <h3>
                        <ChevronRight size={17} />
                        Improvement Suggestions
                      </h3>

                      <ul>
                        {evaluation.improvement_suggestions?.map(
                          (item, index) => (
                            <li key={index}>
                              {item}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                    {/* Ideal Answer */}
                    <div className="evaluation-section">
                      <h3>
                        <CheckCircle2 size={17} />
                        Ideal Answer Points
                      </h3>

                      <ul>
                        {evaluation.ideal_answer_points?.map(
                          (item, index) => (
                            <li key={index}>
                              {item}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                  </div>
                </div>
              )}

            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default InterviewSimulator;