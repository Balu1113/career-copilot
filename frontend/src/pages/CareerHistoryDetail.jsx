import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Brain,
  Briefcase,
  Calendar,
  Loader2,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./CareerAnalysis.css";


function CareerHistoryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    const loadAnalysis = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get(
          `/career/history/${id}/`
        );

        setAnalysis(response.data);
      } catch (err) {
        setError(
          err.response?.data?.error ||
          "Unable to load career analysis."
        );
      } finally {
        setLoading(false);
      }
    };

    loadAnalysis();
  }, [id]);


  if (loading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />

        <main className="dashboard-main career-analysis-page">
          <div className="career-history-loading">
            <Loader2
              size={25}
              className="spinning"
            />

            <p>
              Loading career analysis...
            </p>
          </div>
        </main>
      </div>
    );
  }


  if (error) {
    return (
      <div className="dashboard-layout">
        <Sidebar />

        <main className="dashboard-main career-analysis-page">

          <button
            className="career-back-btn"
            onClick={() =>
              navigate("/career-history")
            }
          >
            <ArrowLeft size={17} />
            Back to History
          </button>

          <div className="career-analysis-error">
            {error}
          </div>

        </main>
      </div>
    );
  }


  if (!analysis) {
    return null;
  }


  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main career-analysis-page">

        <button
          className="career-back-btn"
          onClick={() =>
            navigate("/career-history")
          }
        >
          <ArrowLeft size={17} />
          Back to History
        </button>


        <div className="career-history-detail-header">

          <div className="career-title">
            <Brain size={27} />

            <div>
              <h1>
                Career Analysis
              </h1>

              <p>
                {analysis.resume_title ||
                  "Saved analysis"}
              </p>
            </div>
          </div>


          <div className="career-history-detail-date">
            <Calendar size={15} />

            {new Date(
              analysis.created_at
            ).toLocaleDateString(
              undefined,
              {
                day: "numeric",
                month: "short",
                year: "numeric",
              }
            )}
          </div>

        </div>
        
        <button
          className="career-add-application-btn"
          onClick={() =>
            navigate("/applications", {
              state: {
                fromCareerAnalysis: true,
                analysis,
              },
            })
          }
        >
          <Briefcase size={17} />
          Add to Applications
        </button>


        <div className="career-saved-jd">
          <span>
            Job Description
          </span>

          <p>
            {analysis.job_description}
          </p>
        </div>


        <section className="career-results">

  {analysis.career_recommendation?.match_summary && (
    <section className="result-section match-summary-section">
      <div className="result-section-header">
        <h2>Match Summary</h2>
      </div>

      <div className="match-summary">
        {analysis.career_recommendation.match_summary}
      </div>
    </section>
  )}

  {analysis.resume_intelligence &&
  Object.keys(analysis.resume_intelligence).length > 0 && (
    <ResumeIntelligenceCard
      data={analysis.resume_intelligence}
    />
)}

  <ResultObject
    title="Job Requirements"
    data={
      analysis.job_requirements
    }
  />

          <ResultObject
            title="Resume Analysis"
            data={
              analysis.resume_analysis
            }
          />

          <ResultObject
            title="Skill Gap Analysis"
            data={
              analysis.skill_gap_analysis
            }
          />

          <ResultObject
            title="Career Recommendations"
            data={
              analysis.career_recommendation
            }
          />

          <ResultObject
            title="Interview Preparation"
            data={analysis.interview_preparation}
            analysis={analysis}
          />

        </section>

      </main>
    </div>
  );
}


/* =====================================================
   RESULT OBJECT
===================================================== */

function ResultObject({ title, data, analysis }) {
  if (!data) {
    return null;
  }

  if (title === "Job Requirements") {
    return <JobRequirementsCard data={data} />;
  }

  if (title === "Resume Analysis") {
    return <ResumeAnalysisCard data={data} />;
  }

  if (title === "Skill Gap Analysis") {
    return <SkillGapCard data={data} />;
  }

  if (title === "Career Recommendations") {
    return (
      <CareerRecommendationsCard
        data={data}
      />
    );
  }

  if (title === "Interview Preparation") {
    return (
      <InterviewPreparationCard
        data={data}
        analysis={analysis}
      />
    );
  }

  return null;
}

function ResumeIntelligenceCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Resume Intelligence</h3>

      {data.professional_summary && (
        <div className="career-result-item">
          <span className="result-key">
            Professional Summary
          </span>

          <div className="analysis-explanation">
            {data.professional_summary}
          </div>
        </div>
      )}

      <ResultSection
        title="Skills"
        items={data.skills}
        type="tags"
      />

      <ResultSection
        title="Programming Languages"
        items={data.programming_languages}
        type="tags"
      />

      <ResultSection
        title="Frameworks"
        items={data.frameworks}
        type="tags"
      />

      <ResultSection
        title="Tools & Technologies"
        items={data.tools_and_technologies}
        type="tags"
      />

      <ResultSection
        title="AI / ML Technologies"
        items={data.ai_ml_technologies}
        type="success-tags"
      />

      <ResultSection
        title="Projects"
        items={data.projects}
        type="project-list"
      />

      <ResultSection
        title="Experience"
        items={data.experience}
      />

      <ResultSection
        title="Education"
        items={data.education}
      />

      <ResultSection
        title="Certifications"
        items={data.certifications}
      />
    </div>
  );
}

function JobRequirementsCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Job Requirements</h3>

      <ResultSection
        title="Required Skills"
        items={data.required_skills}
        type="tags"
      />

      <ResultSection
        title="Preferred Skills"
        items={data.preferred_skills}
        type="tags"
      />

      <ResultSection
        title="Responsibilities"
        items={data.responsibilities}
      />

      <ResultSection
        title="Experience Requirements"
        items={data.experience_requirements}
      />

      <ResultSection
        title="Education Requirements"
        items={data.education_requirements}
      />
    </div>
  );
}


function ResumeAnalysisCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Resume Analysis</h3>

      <ResultSection
        title="Matching Skills"
        items={data.matching_skills}
        type="success-tags"
      />

      <ResultSection
        title="Matching Experience"
        items={data.matching_experience}
        type="success-list"
      />

      <ResultSection
        title="Demonstrated Tools"
        items={data.demonstrated_tools}
        type="tags"
      />

      <ResultSection
        title="Relevant Projects"
        items={data.relevant_projects}
        type="project-list"
      />
    </div>
  );
}


function SkillGapCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Skill Gap Analysis</h3>

      <ResultSection
        title="Missing Skills"
        items={data.missing_skills}
        type="danger-tags"
      />

      <ResultSection
        title="Partial Skills"
        items={data.partial_skills}
        type="warning-tags"
      />

      {data.priority_gaps?.length > 0 && (
        <div className="career-result-item">
          <span className="result-key">
            Priority Gaps
          </span>

          <div className="priority-gap-list">
            {data.priority_gaps.map(
              (gap, index) => (
                <div
                  className="priority-gap-card"
                  key={index}
                >
                  <div className="priority-gap-header">
                    <strong>
                      {gap.skill}
                    </strong>

                    <span
                      className={`priority-badge ${String(
                        gap.priority
                      ).toLowerCase()}`}
                    >
                      {gap.priority}
                    </span>
                  </div>

                  <p>
                    {gap.reason}
                  </p>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {data.explanation && (
        <div className="career-result-item">
          <span className="result-key">
            Analysis
          </span>

          <div className="analysis-explanation">
            {data.explanation}
          </div>
        </div>
      )}
    </div>
  );
}



function InterviewPreparationCard({ data, analysis }) {
  const navigate = useNavigate();

  if (!data) {
    return null;
  }

  const hasQuestions =
    data.technical_questions?.length > 0 ||
    data.project_questions?.length > 0 ||
    data.gap_based_questions?.length > 0 ||
    data.behavioral_questions?.length > 0;

  const hasTopics =
    data.preparation_topics?.length > 0;

  if (!hasQuestions && !hasTopics) {
    return null;
  }

  return (
    <div className="career-result-card">
      <h3>Interview Preparation</h3>

      <InterviewQuestionSection
        title="Technical Questions"
        questions={data.technical_questions}
      />

      <InterviewQuestionSection
        title="Project Questions"
        questions={data.project_questions}
      />

      <InterviewQuestionSection
        title="Gap-Based Questions"
        questions={data.gap_based_questions}
      />

      <InterviewQuestionSection
        title="Behavioral Questions"
        questions={data.behavioral_questions}
      />

      {hasTopics && (
        <div className="career-result-item">
          <span className="result-key">
            Preparation Topics
          </span>

          <div className="result-tags">
            {data.preparation_topics.map(
              (topic, index) => (
                <span
                  className="result-tag"
                  key={index}
                >
                  {topic}
                </span>
              )
            )}
          </div>
        </div>
      )}

      <button
        onClick={() =>
          navigate("/interview-practice", {
            state: {
              analysis,
            },
          })
        }
      >
        Practice Interview
      </button>
    </div>
  );
}

function InterviewQuestionSection({
  title,
  questions = [],
}) {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        {title}
      </span>

      <div className="interview-question-list">
        {questions.map((item, index) => (
          <div
            className="interview-question-card"
            key={index}
          >
            <div className="interview-question-header">
              <span className="recommendation-number">
                {index + 1}
              </span>

              <div className="interview-question-meta">
                <span className="result-tag">
                  {item.category}
                </span>

                <span
                  className={`priority-badge ${String(
                    item.difficulty
                  ).toLowerCase()}`}
                >
                  {item.difficulty}
                </span>
              </div>
            </div>

            <div className="interview-question-content">
              <strong>{item.question}</strong>

              {item.reason && (
                <p>
                  <strong>Why:</strong>{" "}
                  {item.reason}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OverallScoreCard({ data }) {
  if (typeof data?.overall_score !== "number") {
    return null;
  }

  const score = Math.min(
    Math.max(data.overall_score, 0),
    100
  );
  const breakdown = data.score_breakdown || {};

  return (
    <div className="overall-score-card">
      <div className="overall-score-top">
        <div className="overall-score-value">
          {score}
          <span>%</span>
        </div>

        <div className="overall-score-copy">
          <span className="result-key">
            Overall Match Score
          </span>

          <strong>
            {data.score_label}
          </strong>

          <p>
            {data.score_summary}
          </p>
        </div>
      </div>

      <div
        className="overall-score-track"
        role="progressbar"
        aria-label="Overall match score"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={score}
      >
        <span style={{ width: `${score}%` }} />
      </div>

      <div className="result-tags overall-score-breakdown">
        <span className="result-tag success">
          {breakdown.demonstrated || 0} demonstrated
        </span>

        <span className="result-tag warning">
          {breakdown.partial || 0} partial
        </span>

        <span className="result-tag danger">
          {breakdown.missing || 0} missing
        </span>

        <span className="result-tag">
          {breakdown.required || 0} required
        </span>

        <span className="result-tag">
          {breakdown.preferred || 0} preferred
        </span>
      </div>

      <p className="overall-score-method">
        Required skills carry twice the weight of preferred skills;
        partial evidence receives half credit.
      </p>
    </div>
  );
}


function CareerRecommendationsCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>
        Career Recommendations
      </h3>

      <OverallScoreCard data={data} />

      <ResultSection
        title="Recommended Topics"
        items={data.recommended_topics}
        type="recommendation-list"
      />

      <ResultSection
        title="Recommended Projects"
        items={data.recommended_projects}
        type="project-list"
      />

      <ResultSection
        title="Interview Preparation"
        items={data.interview_preparation}
        type="recommendation-list"
      />

      <ResultSection
        title="Next Steps"
        items={data.next_steps}
        type="numbered-list"
      />
    </div>
  );
}


function ResultSection({
  title,
  items = [],
  type = "list",
}) {
  const formatTagItem = (item) => {
    if (typeof item === "object" && item !== null) {
      return item.name || item.skill || item.topic || item.title || JSON.stringify(item);
    }
    return item;
  };

  return (
    <div className="career-result-item">
      <span className="result-key">
        {title}
      </span>

      {!items || items.length === 0 ? (
        <p className="result-empty">
          No information available.
        </p>
      ) : type === "tags" ? (
        <div className="result-tags">
          {items.map((item, index) => (
            <span
              className="result-tag"
              key={index}
            >
              {formatTagItem(item)}
            </span>
          ))}
        </div>
      ) : type === "success-tags" ? (
        <div className="result-tags">
          {items.map((item, index) => (
            <span
              className="result-tag success"
              key={index}
            >
              ✓ {formatTagItem(item)}
            </span>
          ))}
        </div>
      ) : type === "danger-tags" ? (
        <div className="result-tags">
          {items.map((item, index) => (
            <span
              className="result-tag danger"
              key={index}
            >
              {formatTagItem(item)}
            </span>
          ))}
        </div>
      ) : type === "warning-tags" ? (
        <div className="result-tags">
          {items.map((item, index) => (
            <span
              className="result-tag warning"
              key={index}
            >
              {formatTagItem(item)}
            </span>
          ))}
        </div>
      ) : type === "project-list" ? (
        <div className="project-list">
          {items.map((item, index) => (
            <div
              className="project-item"
              key={index}
            >
              <div className="project-number">
                {index + 1}
              </div>

              <div style={{ flex: 1 }}>
                {typeof item === "object" && item !== null ? (
                  <div>
                    <strong>{item.name || item.title || "Project"}</strong>
                    {item.description && <p style={{ marginTop: '0.25rem', marginBottom: '0.25rem' }}>{item.description}</p>}
                    {item.purpose && <p style={{ fontSize: '0.9rem', opacity: 0.8, marginTop: '0.25rem' }}><em>Purpose: {item.purpose}</em></p>}
                    {Array.isArray(item.technologies) && item.technologies.length > 0 && (
                      <div className="result-tags" style={{ marginTop: '0.5rem' }}>
                        {item.technologies.map((tech, idx) => (
                          <span key={idx} className="result-tag">
                            {typeof tech === "object" ? (tech.name || JSON.stringify(tech)) : tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p>{item}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : type === "recommendation-list" ? (
        <div className="recommendation-list">
          {items.map((item, index) => (
            <div
              className="recommendation-item"
              key={index}
            >
              <span className="recommendation-icon">
                →
              </span>

              <div style={{ flex: 1 }}>
                {typeof item === "object" && item !== null ? (
                  <div>
                    {item.topic && <strong>{item.topic}</strong>}
                    {item.question && <strong>{item.question}</strong>}
                    {item.name && <strong>{item.name}</strong>}
                    {item.priority && (
                      <span className={`result-tag ${String(item.priority).toLowerCase() === 'high' ? 'danger' : 'warning'}`} style={{ marginLeft: '0.5rem' }}>
                        {item.priority}
                      </span>
                    )}
                    {item.reason && <p style={{ marginTop: '0.25rem' }}>{item.reason}</p>}
                    {item.why && <p style={{ marginTop: '0.25rem', fontSize: '0.9rem', opacity: 0.8 }}><em>Why: {item.why}</em></p>}
                    {item.description && <p style={{ marginTop: '0.25rem' }}>{item.description}</p>}
                    {!item.topic && !item.question && !item.name && !item.reason && !item.why && !item.description && (
                      <p>{formatObject(item)}</p>
                    )}
                  </div>
                ) : (
                  <p>{item}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : type === "numbered-list" ? (
        <div className="recommendation-list">
          {items.map((item, index) => (
            <div
              className="recommendation-item"
              key={index}
            >
              <span className="recommendation-number">
                {index + 1}
              </span>

              <div style={{ flex: 1 }}>
                {typeof item === "object" && item !== null ? (
                  <div>
                    {item.step && <p><strong>{item.step}</strong></p>}
                    {item.action && <p>{item.action}</p>}
                    {item.priority && (
                      <span className="result-tag warning" style={{ marginTop: '0.25rem' }}>
                        {item.priority}
                      </span>
                    )}
                    {!item.step && !item.action && <p>{formatObject(item)}</p>}
                  </div>
                ) : (
                  <p>{item}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <ul>
          {items.map((item, index) => (
            <li key={index}>
              {typeof item === "object" && item !== null
                ? formatObject(item)
                : item}
            </li>
          ))}
        </ul>
      )}

    </div>
  );
}

function formatObject(object) {
  return Object.entries(object)
    .map(([key, value]) => {
      const formattedValue =
        Array.isArray(value)
          ? value.join(", ")
          : typeof value === "object" &&
            value !== null
          ? JSON.stringify(value)
          : value;

      return `${formatKey(key)}: ${formattedValue}`;
    })
    .join(" • ");
}

function formatKey(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

export default CareerHistoryDetail;