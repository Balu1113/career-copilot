import { useEffect, useState } from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  Brain,
  CheckCircle2,
  FileText,
  Lightbulb,
  Loader2,
  Target,
} from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./CareerAnalysis.css";

const stages = [
  {
    key: "resume-intelligence",
    node: "resume_intelligence",
    title: "Resume Intelligence",
    description: "Structuring your resume",
    icon: FileText,
  },
  {
    key: "job",
    node: "job_analyzer",
    title: "Job Analyzer",
    description: "Extracting job requirements",
    icon: Target,
  },
  {
    key: "resume",
    node: "resume_analyzer",
    title: "Resume Analyzer",
    description: "Comparing your resume",
    icon: FileText,
  },
  {
    key: "gap",
    node: "skill_gap",
    title: "Skill Gap Analyzer",
    description: "Identifying missing skills",
    icon: Brain,
  },
  {
    key: "advisor",
    node: "career_advisor",
    title: "Career Advisor",
    description: "Generating recommendations",
    icon: Lightbulb,
  },
  {
    key: "interview-prep",
    node: "interview_prep",
    title: "Interview Prep",
    description: "Preparing interview questions",
    icon: Brain,
  },
];

function CareerAnalysis() {
  const navigate = useNavigate();
  const location = useLocation();
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState(
    location.state?.resumeId || ""
  );

  const [jobDescription, setJobDescription] = useState(
    location.state?.jobDescription || ""
  );

  const [result, setResult] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [currentNode, setCurrentNode] = useState("");
  const [completedNodes, setCompletedNodes] = useState([]);
  const [generating, setGenerating] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    const loadResumes = async () => {
      try {
        const [uploadedResponse, generatedResponse] =
          await Promise.all([
            api.get("/resumes/"),
            api.get("/resume-builder/resumes/"),
          ]);

        const uploaded = uploadedResponse.data.map(
          (resume) => ({
            ...resume,
            type: "uploaded",
            value: `uploaded:${resume.id}`,
            label: resume.title,
          })
        );

        const generated = generatedResponse.data
          .filter(
            (resume) =>
              resume.content &&
              Object.keys(resume.content).length > 0
          )
          .map((resume) => ({
            ...resume,
            type: "generated",
            value: `generated:${resume.id}`,
            label: resume.title,
          }));

        const combined = [...uploaded, ...generated];

        setResumes(combined);

        const incomingId = location.state?.resumeId;

        if (incomingId) {
          setResumeId(
            String(incomingId).includes(":")
              ? String(incomingId)
              : `uploaded:${incomingId}`
          );
        } else if (combined.length > 0) {
          setResumeId(combined[0].value);
        }
      } catch (err) {
        setError("Unable to load resumes.");
      }
    };

    loadResumes();
  }, []);

  const runAnalysis = async (event) => {
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
      setResult(null);
      setAnalysisId(null);
      setError("");
      setCurrentNode("");
      setCompletedNodes([]);

      const token = localStorage.getItem("access_token");

      const [resumeType, selectedResumeId] =
        resumeId.split(":");

      const response = await fetch(
        "http://127.0.0.1:8000/api/career/analyze-stream/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            resume_id: Number(selectedResumeId),
            resume_type:
              resumeType || "uploaded",
            job_description: jobDescription,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.error ||
            data.detail ||
            "Unable to run career analysis."
        );
      }

      if (!response.body) {
        throw new Error(
          "Streaming is not supported by this browser."
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const events = buffer.split("\n\n");

        buffer = events.pop() || "";

        for (const event of events) {
          const line = event
            .split("\n")
            .find((item) => item.startsWith("data:"));

          if (!line) {
            continue;
          }

          const data = JSON.parse(
            line.replace("data:", "").trim()
          );

          if (data.type === "node_started") {
            setCurrentNode(data.node);

            setCompletedNodes((previous) =>
              previous.filter((node) => node !== data.node)
            );
          }

          if (data.type === "node_completed") {
            setCurrentNode(data.node);

            setCompletedNodes((previous) => {
              if (previous.includes(data.node)) {
                return previous;
              }

              return [...previous, data.node];
            });

            if (data.node === "resume_intelligence") {
              setResult((previous) => ({
                ...(previous || {}),
                resume_intelligence:
                  data.data?.resume_intelligence || {},
              }));
            }

            if (data.node === "job_analyzer") {
              setResult((previous) => ({
                ...(previous || {}),
                job_requirements:
                  data.data?.job_requirements || {},
              }));
            }

            if (data.node === "resume_analyzer") {
              setResult((previous) => ({
                ...(previous || {}),
                resume_analysis:
                  data.data?.resume_analysis || {},
              }));
            }

            if (data.node === "skill_gap") {
              setResult((previous) => ({
                ...(previous || {}),
                skill_gap_analysis:
                  data.data?.skill_gap_analysis || {},
              }));
            }

            if (data.node === "career_advisor") {
              setResult((previous) => ({
                ...(previous || {}),
                career_recommendation:
                  data.data?.career_recommendation || {},
              }));
            }

            if (data.node === "interview_prep") {
              setResult((previous) => ({
                ...(previous || {}),
                interview_preparation:
                  data.data?.interview_preparation || {},
              }));
            }
          }

          if (data.type === "completed") {
            setAnalysisId(data.analysis_id);
            setGenerating(false);
          }

          if (
            data.type === "error" ||
            data.type === "workflow_error"
          ) {
            setCurrentNode(data.node || "");

            throw new Error(
              data.message || "Career analysis failed."
            );
          }
        }
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to run career analysis."
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main career-analysis-page">
        <div className="career-analysis-header">
          <div>
            <div className="career-title">
              <Brain size={27} />
              <h1>Agentic Career Analysis</h1>
            </div>

            <p>
              Analyze your resume against a target role using
              a multi-step AI workflow.
            </p>
          </div>
        </div>

        {error && (
          <div className="career-analysis-error">
            {error}
          </div>
        )}

        <section className="career-input-card">
          <div className="career-input-heading">
            <h2>Analyze Job Fit</h2>

            <p>
              Your resume is analyzed against the job description
              using a multi-agent LangGraph workflow.
            </p>
          </div>

          <form onSubmit={runAnalysis}>
            <div className="career-form-group">
              <label>Resume</label>

              <select
                value={resumeId}
                onChange={(event) =>
                  setResumeId(event.target.value)
                }
              >
                {resumes.length === 0 ? (
                  <option value="">
                    No resumes available
                  </option>
                ) : (
                  <>
                    {resumes.some(
                      (resume) =>
                        resume.type === "uploaded"
                    ) && (
                      <optgroup label="Uploaded Resumes">
                        {resumes
                          .filter(
                            (resume) =>
                              resume.type === "uploaded"
                          )
                          .map((resume) => (
                            <option
                              key={resume.value}
                              value={resume.value}
                            >
                              {resume.label}
                            </option>
                          ))}
                      </optgroup>
                    )}

                    {resumes.some(
                      (resume) =>
                        resume.type === "generated"
                    ) && (
                      <optgroup label="Generated Resumes">
                        {resumes
                          .filter(
                            (resume) =>
                              resume.type === "generated"
                          )
                          .map((resume) => (
                            <option
                              key={resume.value}
                              value={resume.value}
                            >
                              {resume.label}
                            </option>
                          ))}
                      </optgroup>
                    )}
                  </>
                )}
              </select>
            </div>

            <div className="career-form-group">
              <label>Job Description</label>

              <textarea
                value={jobDescription}
                onChange={(event) =>
                  setJobDescription(event.target.value)
                }
                rows="9"
                placeholder="Paste the target job description..."
              />
            </div>

            <button
              className="run-analysis-btn"
              type="submit"
              disabled={
                generating || resumes.length === 0
              }
            >
              {generating ? (
                <>
                  <Loader2
                    size={18}
                    className="spinning"
                  />
                  Running AI Agents...
                </>
              ) : (
                <>
                  <Brain size={18} />
                  Run Agentic Analysis
                </>
              )}
            </button>
          </form>
        </section>

        {(generating ||
          result ||
          completedNodes.length > 0 ||
          error) && (
          <section className="agent-pipeline">
            <div className="pipeline-header">
              <div>
                <h2>Agent Pipeline</h2>

                <p>
                  {generating
                    ? "LangGraph is processing your career analysis."
                    : error
                    ? "The agent workflow encountered an error."
                    : "LangGraph completed the career analysis workflow."}
                </p>
              </div>

              {generating && (
                <span className="pipeline-running">
                  <Loader2
                    size={15}
                    className="spinning"
                  />
                  Running
                </span>
              )}
            </div>

            <div className="pipeline">
              {stages.map((stage, index) => {
                const Icon = stage.icon;

                const completed =
                  completedNodes.includes(stage.node);

                const running =
                  generating &&
                  currentNode === stage.node &&
                  !completed;

                const failed =
                  !!error &&
                  currentNode === stage.node &&
                  !completed;

                return (
                  <div
                    className="pipeline-stage-wrapper"
                    key={stage.key}
                  >
                    <div
                      className={`pipeline-stage ${
                        completed
                          ? "completed"
                          : running
                          ? "running"
                          : failed
                          ? "failed"
                          : ""
                      }`}
                    >
                      <div className="pipeline-icon">
                        {completed ? (
                          <CheckCircle2 size={21} />
                        ) : running ? (
                          <Loader2
                            size={21}
                            className="spinning"
                          />
                        ) : failed ? (
                          "!"
                        ) : (
                          <Icon size={21} />
                        )}
                      </div>

                      <div>
                        <h3>{stage.title}</h3>

                        <p>
                          {completed
                            ? "Completed"
                            : running
                            ? "Processing..."
                            : failed
                            ? "Failed"
                            : stage.description}
                        </p>
                      </div>
                    </div>

                    {index < stages.length - 1 && (
                      <div
                        className={`pipeline-connector ${
                          completed ? "active" : ""
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {result && (
          <section className="career-results">
            <div className="career-result-header">
              <div>
                <h2>Career Analysis</h2>

                <p>
                  Results generated by the agentic workflow.
                </p>
              </div>

              <CheckCircle2 size={27} />
            </div>

            {result?.career_recommendation?.match_summary && (
              <div className="match-summary-section">
                <h3>Match Summary</h3>

                <div className="match-summary">
                  {result.career_recommendation.match_summary}
                </div>
              </div>
            )}

            {result.resume_intelligence &&
              Object.keys(result.resume_intelligence).length > 0 && (
                <ResultObject
                  title="Resume Intelligence"
                  data={result.resume_intelligence}
                />
              )}

            <ResultObject
              title="Job Requirements"
              data={result.job_requirements}
            />

            <ResultObject
              title="Resume Analysis"
              data={result.resume_analysis}
            />

            <ResultObject
              title="Skill Gap Analysis"
              data={result.skill_gap_analysis}
            />

            <ResultObject
              title="Career Recommendations"
              data={result.career_recommendation}
            />

            <ResultObject
              title="Interview Preparation"
              data={result.interview_preparation}
              analysis={result}
              analysisId={analysisId}
            />
          </section>
        )}
      </main>
    </div>
  );
}

function ResultObject({ title, data, analysis, analysisId }) {
  if (!data) {
    return null;
  }

  if (title === "Resume Intelligence") {
    return <ResumeIntelligenceCard data={data} />;
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
    return <CareerRecommendationsCard data={data} />;
  }

  if (title === "Interview Preparation") {
    return (
      <InterviewPreparationCard
        data={data}
        analysis={analysis}
        analysisId={analysisId}
      />
    );
  }

  return null;
}

/* =====================================================
   RESUME INTELLIGENCE
===================================================== */

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

      <ResumeProjects projects={data.projects} />

      <ResultSection
        title="Experience"
        items={data.experience}
      />

      <ResumeEducation
        education={data.education}
      />

      <ResumeCertifications
        certifications={data.certifications}
      />
    </div>
  );
}

function ResumeProjects({ projects = [] }) {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Projects
      </span>

      <div className="project-list">
        {projects.map((project, index) => (
          <div
            className="project-item"
            key={index}
          >
            <div className="project-number">
              {index + 1}
            </div>

            <div className="project-content">
              <h4>{project.name}</h4>

              {project.description?.length > 0 && (
                <ul>
                  {project.description.map(
                    (description, descriptionIndex) => (
                      <li key={descriptionIndex}>
                        {description}
                      </li>
                    )
                  )}
                </ul>
              )}

              {project.technologies?.length > 0 && (
                <div className="project-technologies">
                  <strong>Technologies:</strong>

                  <div className="result-tags">
                    {project.technologies.map(
                      (technology, technologyIndex) => (
                        <span
                          className="result-tag"
                          key={technologyIndex}
                        >
                          {technology}
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResumeEducation({ education = [] }) {
  if (!education || education.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Education
      </span>

      <div className="structured-result-list">
        {education.map((item, index) => (
          <div
            className="structured-result-item"
            key={index}
          >
            <h4>{item.degree}</h4>

            <p>{item.institution}</p>

            {item.dates && (
              <span className="structured-result-meta">
                {item.dates}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ResumeCertifications({
  certifications = [],
}) {
  if (!certifications || certifications.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Certifications
      </span>

      <div className="structured-result-list">
        {certifications.map((item, index) => (
          <div
            className="structured-result-item"
            key={index}
          >
            <h4>{item.name}</h4>

            {item.issuer && (
              <p>{item.issuer}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* =====================================================
   JOB REQUIREMENTS
===================================================== */

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

/* =====================================================
   RESUME ANALYSIS
===================================================== */

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

/* =====================================================
   SKILL GAP
===================================================== */

function SkillGapCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Skill Gap Analysis</h3>

      <SkillGapList
        title="Missing Skills"
        items={data.missing_skills}
      />

      <SkillGapList
        title="Partial Skills"
        items={data.partial_skills}
      />

      {data.priority_gaps?.length > 0 && (
        <div className="career-result-item">
          <span className="result-key">
            Priority Gaps
          </span>

          <div className="priority-gap-list">
            {data.priority_gaps.map((gap, index) => (
              <div
                className="priority-gap-card"
                key={index}
              >
                <div className="priority-gap-header">
                  <strong>{gap.skill}</strong>

                  <span
                    className={`priority-badge ${String(
                      gap.priority
                    ).toLowerCase()}`}
                  >
                    {gap.priority}
                  </span>
                </div>

                {gap.reason && (
                  <p>{gap.reason}</p>
                )}
              </div>
            ))}
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

function SkillGapList({ title, items = [] }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        {title}
      </span>

      <div className="priority-gap-list">
        {items.map((item, index) => (
          <div
            className="priority-gap-card"
            key={index}
          >
            <div className="priority-gap-header">
              <strong>{item.skill}</strong>

              <span
                className={`priority-badge ${String(
                  item.priority
                ).toLowerCase()}`}
              >
                {item.priority}
              </span>
            </div>

            {item.reason && (
              <p>{item.reason}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* =====================================================
   CAREER RECOMMENDATIONS
===================================================== */

function CareerRecommendationsCard({ data }) {
  return (
    <div className="career-result-card">
      <h3>Career Recommendations</h3>

      {data.match_summary && (
        <div className="career-result-item">
          <span className="result-key">Match Summary</span>

          <div className="analysis-explanation">
            {data.match_summary}
          </div>
        </div>
      )}

      <RecommendationTopics
        items={data.recommended_topics}
      />

      <RecommendedProjects
        projects={data.recommended_projects}
      />

      <NextSteps
        items={data.next_steps}
      />
    </div>
  );
}

function RecommendationTopics({ items = [] }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Recommended Topics
      </span>

      <div className="priority-gap-list">
        {items.map((item, index) => (
          <div
            className="priority-gap-card"
            key={index}
          >
            <div className="priority-gap-header">
              <strong>{item.topic}</strong>

              <span
                className={`priority-badge ${String(
                  item.priority
                ).toLowerCase()}`}
              >
                {item.priority}
              </span>
            </div>

            {item.reason && (
              <p>{item.reason}</p>
            )}

            {item.source_gaps?.length > 0 && (
              <div className="source-gaps">
                <span className="source-gaps-label">
                  Source gaps
                </span>

                <div className="result-tags">
                  {item.source_gaps.map(
                    (gap, gapIndex) => (
                      <span
                        className="result-tag warning"
                        key={gapIndex}
                      >
                        {gap}
                      </span>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


function RecommendedProjects({ projects = [] }) {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Recommended Projects
      </span>

      <div className="project-list">
        {projects.map((project, index) => (
          <div
            className="project-item"
            key={index}
          >
            <div className="project-number">
              {index + 1}
            </div>

            <div className="project-content">
              <h4>{project.name}</h4>

              {project.description && (
                <p>{project.description}</p>
              )}

              {project.technologies?.length > 0 && (
                <div className="project-technologies">
                  <strong>Technologies:</strong>

                  <div className="result-tags">
                    {project.technologies.map(
                      (technology, technologyIndex) => (
                        <span
                          className="result-tag"
                          key={technologyIndex}
                        >
                          {technology}
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


function InterviewPreparationCard({ data, analysis, analysisId }) {
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

      <button
        onClick={() =>
          navigate("/interview-practice", {
            state: {
              analysis: {
                ...analysis,
                id: analysisId,
              },
            },
          })
        }
      >
        Practice Interview
      </button>
      {hasTopics && (
        <div className="career-result-item">
          <span className="result-key">
            Preparation Topics
          </span>

          <div className="result-tags">
            {data.preparation_topics.map((topic, index) => (
              <span
                className="result-tag"
                key={index}
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}
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
                  <strong>Why:</strong> {item.reason}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}



function NextSteps({ items = [] }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="career-result-item">
      <span className="result-key">
        Next Steps
      </span>

      <div className="priority-gap-list">
        {items.map((item, index) => (
          <div
            className="priority-gap-card"
            key={index}
          >
            <div className="priority-gap-header">
              <strong>
                {index + 1}. {item.step}
              </strong>

              <span
                className={`priority-badge ${String(
                  item.priority
                ).toLowerCase()}`}
              >
                {item.priority}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* =====================================================
   GENERIC RESULT SECTION
===================================================== */

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

export default CareerAnalysis;