import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  Calendar,
  ChevronRight,
  FileText,
  Loader2,
  Trash2,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./CareerHistory.css";


function CareerHistory() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  


  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get(
          "/career/history/"
        );

        setAnalyses(response.data);
      } catch (err) {
        setError(
          err.response?.data?.error ||
          "Unable to load career analysis history."
        );
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);


  const getSkillGapCount = (analysis) => {
    return (
      analysis.skill_gap_analysis?.missing_skills
        ?.length || 0
    );
  };


  const getJobTitle = (analysis) => {
    const requirements =
      analysis.job_requirements || {};

    const responsibilities =
      requirements.responsibilities || [];

    if (responsibilities.length > 0) {
      return responsibilities[0];
    }

    return "Career Analysis";
  };


  const formatDate = (date) => {
    if (!date) {
      return "Unknown date";
    }

    return new Date(date).toLocaleDateString(
      undefined,
      {
        day: "numeric",
        month: "short",
        year: "numeric",
      }
    );
  };

  const deleteAnalysis = async (id) => {
  const confirmed = window.confirm(
    "Are you sure you want to delete this career analysis?"
  );

  if (!confirmed) {
    return;
  }

  try {
    setDeletingId(id);
    setError("");

    await api.delete(
      `/career/history/${id}/`
    );

    setAnalyses((previous) =>
      previous.filter(
        (analysis) => analysis.id !== id
      )
    );
  } catch (err) {
    setError(
      err.response?.data?.error ||
      "Unable to delete career analysis."
    );
  } finally {
    setDeletingId(null);
  }
};

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main career-history-page">

        <div className="career-history-header">
          <div className="career-history-title">
            <Brain size={27} />

            <div>
              <h1>Career Analysis History</h1>

              <p>
                View your previously generated career
                analyses.
              </p>
            </div>
          </div>
        </div>


        {error && (
          <div className="career-history-error">
            {error}
          </div>
        )}


        {loading ? (
          <div className="career-history-loading">
            <Loader2
              size={25}
              className="spinning"
            />

            <p>
              Loading your career analyses...
            </p>
          </div>
        ) : analyses.length === 0 ? (
          <div className="career-history-empty">
            <FileText size={40} />

            <h2>
              No Career Analyses Yet
            </h2>

            <p>
              Run a career analysis against a job
              description to see it here.
            </p>
          </div>
        ) : (
          <div className="career-history-list">

            {analyses.map((analysis) => (
              <div
                className="career-history-card"
                key={analysis.id}
                onClick={() =>
                    navigate(`/career-history/${analysis.id}`)
                }
                >

                <div className="career-history-card-icon">
                  <Brain size={21} />
                </div>


                <div className="career-history-card-content">

                  <div className="career-history-card-top">

                    <div>
                      <h2>
                        {analysis.resume_title ||
                          "Resume Analysis"}
                      </h2>

                      <p className="career-history-role">
                        {getJobTitle(analysis)}
                      </p>
                    </div>

                    <div className="career-history-actions">
  <button
    className="career-view-btn"
    onClick={(event) => {
      event.stopPropagation();

      navigate(
        `/career-history/${analysis.id}`
      );
    }}
  >
    View Analysis
  </button>

  <button
    className="career-delete-btn"
    disabled={deletingId === analysis.id}
    onClick={(event) => {
      event.stopPropagation();

      deleteAnalysis(analysis.id);
    }}
  >
    {deletingId === analysis.id ? (
      <Loader2
        size={15}
        className="spinning"
      />
    ) : (
      <Trash2 size={15} />
    )}

    Delete
  </button>
</div>

                  </div>


                  <div className="career-history-meta">

                    <span>
                      <Calendar size={14} />

                      {formatDate(
                        analysis.created_at
                      )}
                    </span>

                    <span>
                      <FileText size={14} />

                      {analysis.resume_title}
                    </span>

                    <span>
                      <Brain size={14} />

                      {getSkillGapCount(
                        analysis
                      )}{" "}
                      skill gaps
                    </span>

                  </div>


                  <div className="career-history-description">
                  {analysis.job_description}
                </div>

                {analysis.career_recommendation?.match_summary && (
                  <div className="history-match-summary">
                    <span className="history-summary-label">
                      Match Summary
                    </span>

                    <p>
                      {analysis.career_recommendation.match_summary}
                    </p>
                  </div>
                )}

                </div>

              </div>
            ))}

          </div>
        )}

      </main>
    </div>
  );
}


export default CareerHistory;