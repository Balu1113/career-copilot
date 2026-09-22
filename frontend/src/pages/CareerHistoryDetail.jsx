import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Brain,
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

        </section>

      </main>
    </div>
  );
}


/* =====================================================
   RESULT OBJECT
===================================================== */

function ResultObject({ title, data }) {
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


function CareerRecommendationsCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>
        Career Recommendations
      </h3>

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
              {item}
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
              ✓ {item}
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
              {item}
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
              {item}
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

              <p>{item}</p>
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

              <p>{item}</p>
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

              <p>{item}</p>
            </div>
          ))}
        </div>
      ) : (
        <ul>
          {items.map((item, index) => (
            <li key={index}>
              {item}
            </li>
          ))}
        </ul>
      )}

    </div>
  );
}


export default CareerHistoryDetail;