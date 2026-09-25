import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Clock3,
  Lightbulb,
  MessageSquare,
  Play,
  RefreshCw,
  Target,
  Trophy,
  XCircle,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import api from "../services/api";
import "./InterviewPerformance.css";

function formatDate(dateValue) {
  if (!dateValue) {
    return "Recently";
  }

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getScoreClass(score) {
  if (score >= 80) {
    return "strong";
  }

  if (score >= 70) {
    return "steady";
  }

  return "focus";
}

function InterviewPerformance() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        "/career/interview/analytics/",
      );

      setAnalytics(response.data);
    } catch (err) {
      console.error(
        "Failed to load interview performance:",
        err,
      );

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to load interview performance.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadAnalytics();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadAnalytics]);

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar />

        <main className="main-content">
          <div className="interview-performance-page">
            <div className="performance-loading">
              <BarChart3 size={30} />
              <h2>Loading your performance...</h2>
              <p>
                Calculating interview insights from your saved
                responses.
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const summary = analytics?.summary || {};
  const categories =
    analytics?.performance_by_category || [];
  const recentScores = analytics?.recent_scores || [];
  const weakAreas = analytics?.weak_areas || [];
  const recommendedFocus =
    analytics?.recommended_focus || [];
  const hasInterviewData =
    (summary.total_interviews || 0) > 0 ||
    (summary.questions_answered || 0) > 0;
  const overallAverage = summary.overall_average;

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <div className="interview-performance-page">
          <div className="performance-header">
            <button
              className="performance-back-button"
              onClick={() => navigate("/dashboard")}
            >
              <ArrowLeft size={17} />
              Dashboard
            </button>

            <div className="performance-title-row">
              <div className="performance-title-icon">
                <BarChart3 size={24} />
              </div>

              <div>
                <span>Interview Analytics</span>
                <h1>Interview Performance</h1>
                <p>
                  Turn your saved interview answers into clear,
                  actionable improvement priorities.
                </p>
              </div>
            </div>

            <div className="performance-header-actions">
              <button
                className="performance-secondary-button"
                onClick={() =>
                  navigate("/interview-history")
                }
              >
                <Clock3 size={16} />
                View History
              </button>

              <button
                className="performance-primary-button"
                onClick={() =>
                  navigate("/interview-simulator")
                }
              >
                <Play size={16} />
                Practice Interview
              </button>
            </div>
          </div>

          {error && (
            <div className="performance-error">
              <XCircle size={18} />

              <div>
                <strong>Performance data unavailable</strong>
                <span>{error}</span>
              </div>

              <button onClick={loadAnalytics}>
                <RefreshCw size={15} />
                Retry
              </button>
            </div>
          )}

          {!error && !hasInterviewData ? (
            <div className="performance-empty-card">
              <div className="performance-empty-icon">
                <Target size={32} />
              </div>

              <span>No Performance Yet</span>
              <h2>Complete an interview to begin</h2>
              <p>
                Your category scores, recent results, weak areas,
                and recommended focus will appear here.
              </p>

              <button
                className="performance-primary-button"
                onClick={() =>
                  navigate("/interview-simulator")
                }
              >
                <Play size={17} />
                Start Interview
              </button>
            </div>
          ) : hasInterviewData ? (
            <>
              <section className="performance-summary-grid">
                <div className="performance-summary-card score-card">
                  <div className="performance-summary-icon">
                    <Trophy size={21} />
                  </div>

                  <div>
                    <span>Overall Average</span>
                    <strong>
                      {overallAverage ?? "—"}
                      {overallAverage !== null &&
                      overallAverage !== undefined ? (
                        <small>/100</small>
                      ) : null}
                    </strong>
                    <p>
                      Completed interview score average
                    </p>
                  </div>
                </div>

                <div className="performance-summary-card">
                  <div className="performance-summary-icon completed">
                    <CheckCircle2 size={21} />
                  </div>

                  <div>
                    <span>Completed Interviews</span>
                    <strong>
                      {summary.completed_interviews || 0}
                    </strong>
                    <p>
                      {summary.in_progress_interviews || 0}{" "}
                      currently in progress
                    </p>
                  </div>
                </div>

                <div className="performance-summary-card">
                  <div className="performance-summary-icon answers">
                    <MessageSquare size={21} />
                  </div>

                  <div>
                    <span>Questions Answered</span>
                    <strong>
                      {summary.questions_answered || 0}
                    </strong>
                    <p>
                      Average answer score:{" "}
                      {summary.average_answer_score ?? "—"}
                      {summary.average_answer_score !== null &&
                      summary.average_answer_score !== undefined
                        ? "/100"
                        : ""}
                    </p>
                  </div>
                </div>
              </section>

              <section className="performance-main-grid">
                <div className="performance-panel category-panel">
                  <div className="performance-panel-header">
                    <div>
                      <span>Performance Breakdown</span>
                      <h2>Performance by Category</h2>
                    </div>

                    <Target size={20} />
                  </div>

                  {categories.length > 0 ? (
                    <div className="category-performance-list">
                      {categories.map((category) => (
                        <div
                          className="category-performance-item"
                          key={category.category}
                        >
                          <div className="category-performance-meta">
                            <div>
                              <strong>
                                {category.category}
                              </strong>
                              <span>
                                {
                                  category.questions_answered
                                }{" "}
                                question
                                {category.questions_answered ===
                                1
                                  ? ""
                                  : "s"}
                              </span>
                            </div>

                            <div
                              className={`category-score ${getScoreClass(
                                category.average_score,
                              )}`}
                            >
                              {category.average_score}
                              <span>/100</span>
                            </div>
                          </div>

                          <div className="category-score-track">
                            <span
                              className={getScoreClass(
                                category.average_score,
                              )}
                              style={{
                                width: `${Math.min(
                                  Math.max(
                                    category.average_score,
                                    0,
                                  ),
                                  100,
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="performance-panel-empty">
                      <Target size={23} />
                      <p>
                        Category scores appear after your first
                        evaluated answer.
                      </p>
                    </div>
                  )}
                </div>

                <div className="performance-panel recent-panel">
                  <div className="performance-panel-header">
                    <div>
                      <span>Score Trend</span>
                      <h2>Recent Scores</h2>
                    </div>

                    <BarChart3 size={20} />
                  </div>

                  {recentScores.length > 0 ? (
                    <div className="recent-score-list">
                      {recentScores.map((item, index) => (
                        <div
                          className="recent-score-item"
                          key={item.session_id}
                        >
                          <div className="recent-score-number">
                            {index + 1}
                          </div>

                          <div className="recent-score-copy">
                            <strong>Interview {index + 1}</strong>
                            <span>
                              {item.target_role ||
                                "Career Interview"}{" "}
                              · {formatDate(item.completed_at)}
                            </span>
                          </div>

                          <div
                            className={`recent-score-value ${getScoreClass(
                              item.score,
                            )}`}
                          >
                            {item.score}
                            <span>/100</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="performance-panel-empty">
                      <BarChart3 size={23} />
                      <p>
                        Complete an interview to start your
                        recent score trend.
                      </p>
                    </div>
                  )}
                </div>
              </section>

              <section className="performance-insight-grid">
                <div className="performance-panel weak-areas-panel">
                  <div className="performance-panel-header">
                    <div>
                      <span>Improvement Opportunities</span>
                      <h2>Weak Areas</h2>
                    </div>

                    <AlertTriangle size={20} />
                  </div>

                  {weakAreas.length > 0 ? (
                    <div className="weak-area-list">
                      {weakAreas.map((area) => (
                        <div
                          className="weak-area-item"
                          key={`${area.source}-${area.name}`}
                        >
                          <div className="weak-area-icon">
                            <AlertTriangle size={16} />
                          </div>

                          <div>
                            <strong>{area.name}</strong>
                            <span>
                              {area.average_score}/100 average ·{" "}
                              {area.questions_answered} low-scoring
                              question
                              {area.questions_answered === 1
                                ? ""
                                : "s"}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="performance-panel-empty success">
                      <CheckCircle2 size={24} />
                      <p>
                        No significant weak areas detected yet.
                        Keep practicing to build consistency.
                      </p>
                    </div>
                  )}
                </div>

                <div className="performance-panel focus-panel">
                  <div className="performance-panel-header">
                    <div>
                      <span>Next Best Actions</span>
                      <h2>Recommended Focus</h2>
                    </div>

                    <Lightbulb size={20} />
                  </div>

                  <div className="recommended-focus-list">
                    {recommendedFocus.map((item, index) => (
                      <div
                        className="recommended-focus-item"
                        key={item.title}
                      >
                        <div className="focus-step">
                          {index + 1}
                        </div>

                        <div>
                          <strong>{item.title}</strong>
                          <p>{item.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <div className="performance-next-step-card">
                <div className="performance-next-step-icon">
                  <Target size={23} />
                </div>

                <div>
                  <span>Keep Improving</span>
                  <h2>
                    Turn weak areas into stronger answers
                  </h2>
                  <p>
                    Review the recommended focus, then practice
                    again with resume-grounded interview questions.
                  </p>
                </div>

                <button
                  className="performance-primary-button"
                  onClick={() =>
                    navigate("/interview-simulator")
                  }
                >
                  <Play size={16} />
                  Practice Again
                </button>
              </div>
            </>
          ) : null}
        </div>
      </main>
    </div>
  );
}

export default InterviewPerformance;
