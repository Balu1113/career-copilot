import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock3,
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
import "./InterviewHistory.css";

function formatDate(dateValue) {
  if (!dateValue) {
    return "—";
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}

function formatInterviewType(type) {
  if (!type) {
    return "Mixed";
  }

  return type
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function InterviewHistory() {
  const navigate = useNavigate();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedSession, setExpandedSession] =
    useState(null);

  const inProgressSessions = sessions.filter(
    (session) => !session.completed,
  );
  const latestInProgressSession =
    inProgressSessions[0] || null;

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        "/career/interview/history/",
      );

      setSessions(response.data || []);
    } catch (err) {
      console.error(
        "Failed to load interview history:",
        err,
      );

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to load interview history.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadHistory();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadHistory]);

  const toggleSession = (sessionId) => {
    setExpandedSession((previous) =>
      previous === sessionId
        ? null
        : sessionId,
    );
  };

  const handleContinue = (session) => {
    navigate("/interview-simulator", {
      state: {
        sessionId: session.id,
        analysisId: session.career_analysis_id,
        targetRole: session.target_role,
      },
    });
  };

  const handlePracticeAgain = (session) => {
    navigate("/interview-simulator", {
      state: {
        analysisId:
          session.career_analysis_id,
        targetRole: session.target_role,
      },
    });
  };

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="interview-history-page">

          {/* Header */}
          <div className="interview-history-header">
            <button
              className="history-back-button"
              onClick={() => navigate("/dashboard")}
            >
              <ArrowLeft size={17} />
              Dashboard
            </button>

            <div className="history-title-row">
              <div className="history-title-icon">
                <MessageSquare size={23} />
              </div>

              <div>
                <h1>Interview History</h1>

                <p>
                  Review your previous interview
                  sessions, scores, and AI feedback.
                </p>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="history-error">
              <XCircle size={17} />
              <span>{error}</span>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="history-loading">
              <Loader2
                size={28}
                className="history-spin"
              />

              <p>
                Loading your interview history...
              </p>
            </div>
          ) : sessions.length === 0 ? (

            /* Empty State */
            <div className="history-empty-card">
              <div className="history-empty-icon">
                <MessageSquare size={30} />
              </div>

              <h2>
                No interview sessions yet
              </h2>

              <p>
                Complete an interview simulation to
                see your scores and AI feedback here.
              </p>

              <button
                className="history-primary-button"
                onClick={() =>
                  navigate(
                    "/interview-simulator",
                  )
                }
              >
                Start Interview
              </button>
            </div>

          ) : (

            /* History */
            <div className="history-content">

              <div className="history-summary-card">
                <div className="history-summary-item">
                  <MessageSquare size={20} />

                  <div>
                    <span>Total Sessions</span>
                    <strong>{sessions.length}</strong>
                  </div>
                </div>

                <div className="history-summary-item">
                  <CheckCircle2 size={20} />

                  <div>
                    <span>Completed</span>

                    <strong>
                      {
                        sessions.filter(
                          (session) =>
                            session.completed,
                        ).length
                      }
                    </strong>
                  </div>
                </div>

                <div className="history-summary-item">
                  <Trophy size={20} />

                  <div>
                    <span>Average Score</span>

                    <strong>
                      {(() => {
                        const completed =
                          sessions.filter(
                            (session) =>
                              session.completed &&
                              session.overall_score !==
                                null &&
                              session.overall_score !==
                                undefined,
                          );

                        if (
                          completed.length === 0
                        ) {
                          return "—";
                        }

                        const average =
                          completed.reduce(
                            (sum, session) =>
                              sum +
                              session.overall_score,
                            0,
                          ) /
                          completed.length;

                        return `${Math.round(
                          average,
                        )}/100`;
                      })()}
                    </strong>
                  </div>
                </div>
              </div>

              {latestInProgressSession && (
                <div className="history-resume-card">
                  <div className="history-resume-icon">
                    <Play size={22} />
                  </div>

                  <div className="history-resume-copy">
                    <span>Interview in Progress</span>

                    <h2>
                      Continue your{" "}
                      {latestInProgressSession.target_role ||
                        "career interview"}
                    </h2>

                    <p>
                      {inProgressSessions.length > 1
                        ? `${inProgressSessions.length} active sessions. `
                        : ""}
                      Question{" "}
                      {Math.min(
                        latestInProgressSession.current_question_index +
                          1,
                        latestInProgressSession.total_questions,
                      )}{" "}
                      of {latestInProgressSession.total_questions} ·{" "}
                      {
                        latestInProgressSession.answered_questions
                      }{" "}
                      answered
                    </p>
                  </div>

                  <button
                    className="history-resume-button"
                    onClick={() =>
                      handleContinue(
                        latestInProgressSession,
                      )
                    }
                  >
                    <Play size={16} />
                    Continue Interview
                  </button>
                </div>
              )}

              <div className="history-list">
                {sessions.map((session) => {
                  const isExpanded =
                    expandedSession ===
                    session.id;

                  return (
                    <div
                      className="history-session-card"
                      key={session.id}
                    >

                      {/* Session Header */}
                      <button
                        type="button"
                        className="history-session-header"
                        onClick={() =>
                          toggleSession(
                            session.id,
                          )
                        }
                      >
                        <div className="history-session-main">

                          <div className="history-session-icon">
                            <MessageSquare
                              size={20}
                            />
                          </div>

                          <div>
                            <h2>
                              {session.target_role ||
                                "Career Interview"}
                            </h2>

                            <div className="history-session-meta">
                              <span>
                                {formatInterviewType(
                                  session.interview_type,
                                )}
                              </span>

                              <span>
                                <Clock3
                                  size={13}
                                />

                                {formatDate(
                                  session.created_at,
                                )}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="history-session-right">

                          {session.completed ? (
                            <div className="history-score">
                              <Trophy size={17} />

                              <strong>
                                {session.overall_score ??
                                  0}
                              </strong>

                              <span>
                                /100
                              </span>
                            </div>
                          ) : (
                            <span className="history-incomplete">
                              In Progress
                            </span>
                          )}

                          {isExpanded ? (
                            <ChevronUp size={19} />
                          ) : (
                            <ChevronDown size={19} />
                          )}
                        </div>
                      </button>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="history-session-details">

                          <div className="history-detail-grid">

                            <div className="history-detail-item">
                              <Target size={17} />

                              <div>
                                <span>
                                  Target Role
                                </span>

                                <strong>
                                  {session.target_role ||
                                    "Not specified"}
                                </strong>
                              </div>
                            </div>

                            <div className="history-detail-item">
                              <MessageSquare
                                size={17}
                              />

                              <div>
                                <span>
                                  Questions
                                </span>

                                <strong>
                                  {
                                    session.answered_questions
                                  }{" "}
                                  /{" "}
                                  {
                                    session.total_questions
                                  }
                                </strong>
                              </div>
                            </div>

                            <div className="history-detail-item">
                              <Trophy size={17} />

                              <div>
                                <span>
                                  Overall Score
                                </span>

                                <strong>
                                  {session.overall_score ??
                                    "—"}
                                  {session.overall_score !==
                                    null &&
                                  session.overall_score !==
                                    undefined
                                    ? "/100"
                                    : ""}
                                </strong>
                              </div>
                            </div>

                            <div className="history-detail-item">
                              <Clock3 size={17} />

                              <div>
                                <span>
                                  Completed
                                </span>

                                <strong>
                                  {session.completed
                                    ? formatDate(
                                        session.completed_at,
                                      )
                                    : "Not completed"}
                                </strong>
                              </div>
                            </div>

                          </div>

                          {/* Responses */}
                          {session.responses?.length >
                            0 && (
                            <div className="history-responses">

                              <h3>
                                Question Feedback
                              </h3>

                              {session.responses.map(
                                (response) => (
                                  <div
                                    className="history-response-card"
                                    key={response.id}
                                  >

                                    <div className="response-header">
                                      <div>
                                        <span className="response-number">
                                          Question{" "}
                                          {response.question_index +
                                            1}
                                        </span>

                                        <span className="response-category">
                                          {
                                            response.category
                                          }
                                        </span>

                                        <span className="response-difficulty">
                                          {
                                            response.difficulty
                                          }
                                        </span>
                                      </div>

                                      <div className="response-score">
                                        {response.score ??
                                          "—"}
                                        {response.score !==
                                          null &&
                                        response.score !==
                                          undefined
                                          ? "/100"
                                          : ""}
                                      </div>
                                    </div>

                                    <div className="response-question">
                                      <strong>
                                        Question
                                      </strong>

                                      <p>
                                        {
                                          response.question
                                        }
                                      </p>
                                    </div>

                                    <div className="response-answer">
                                      <strong>
                                        Your Answer
                                      </strong>

                                      <p>
                                        {
                                          response.answer
                                        }
                                      </p>
                                    </div>

                                    {response.evaluation && (
                                      <div className="response-evaluation">

                                        {response.evaluation
                                          .strengths
                                          ?.length >
                                          0 && (
                                          <div className="feedback-block">
                                            <h4>
                                              Strengths
                                            </h4>

                                            <ul>
                                              {response.evaluation.strengths.map(
                                                (
                                                  item,
                                                  index,
                                                ) => (
                                                  <li
                                                    key={
                                                      index
                                                    }
                                                  >
                                                    {item}
                                                  </li>
                                                ),
                                              )}
                                            </ul>
                                          </div>
                                        )}

                                        {response.evaluation
                                          .missing_points
                                          ?.length >
                                          0 && (
                                          <div className="feedback-block">
                                            <h4>
                                              Missing Points
                                            </h4>

                                            <ul>
                                              {response.evaluation.missing_points.map(
                                                (
                                                  item,
                                                  index,
                                                ) => (
                                                  <li
                                                    key={
                                                      index
                                                    }
                                                  >
                                                    {item}
                                                  </li>
                                                ),
                                              )}
                                            </ul>
                                          </div>
                                        )}

                                        {response.evaluation
                                          .improvement_suggestions
                                          ?.length >
                                          0 && (
                                          <div className="feedback-block">
                                            <h4>
                                              Improvement Suggestions
                                            </h4>

                                            <ul>
                                              {response.evaluation.improvement_suggestions.map(
                                                (
                                                  item,
                                                  index,
                                                ) => (
                                                  <li
                                                    key={
                                                      index
                                                    }
                                                  >
                                                    {item}
                                                  </li>
                                                ),
                                              )}
                                            </ul>
                                          </div>
                                        )}

                                        {response.evaluation
                                          .ideal_answer_points
                                          ?.length >
                                          0 && (
                                          <div className="feedback-block">
                                            <h4>
                                              Ideal Answer Points
                                            </h4>

                                            <ul>
                                              {response.evaluation.ideal_answer_points.map(
                                                (
                                                  item,
                                                  index,
                                                ) => (
                                                  <li
                                                    key={
                                                      index
                                                    }
                                                  >
                                                    {item}
                                                  </li>
                                                ),
                                              )}
                                            </ul>
                                          </div>
                                        )}

                                      </div>
                                    )}
                                  </div>
                                ),
                              )}
                            </div>
                          )}

                          <div className="history-session-actions">
                            {!session.completed && (
                              <button
                                className="history-continue-button"
                                onClick={() =>
                                  handleContinue(session)
                                }
                              >
                                <Play size={16} />
                                Continue Interview
                              </button>
                            )}

                            <button
                              className="history-secondary-button"
                              onClick={() =>
                                handlePracticeAgain(
                                  session,
                                )
                              }
                            >
                              <RotateCcw size={16} />
                              Practice Again
                            </button>
                          </div>

                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default InterviewHistory;