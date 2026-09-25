import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Code2,
  Loader2,
  Map,
  Sparkles,
  Target,
} from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./CareerRoadmap.css";

function getAnalysisLabel(analysis) {
  const descriptionLine =
    analysis.job_description
      ?.split("\n")
      .map((line) => line.trim())
      .find(Boolean) || "Saved career analysis";
  const shortenedDescription =
    descriptionLine.length > 70
      ? `${descriptionLine.slice(0, 67)}...`
      : descriptionLine;
  const date = analysis.created_at
    ? new Date(analysis.created_at).toLocaleDateString()
    : "";

  return [
    analysis.resume_title || `Analysis #${analysis.id}`,
    shortenedDescription,
    date,
  ]
    .filter(Boolean)
    .join(" · ");
}

function CareerRoadmap() {
  const navigate = useNavigate();

  const [roadmaps, setRoadmaps] = useState([]);
  const [selectedRoadmap, setSelectedRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysisId, setSelectedAnalysisId] =
    useState("");
  const [targetRole, setTargetRole] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const loadRoadmap = useCallback(async (roadmapId) => {
    try {
      setDetailLoading(true);
      setError("");

      const response = await api.get(
        `/career/roadmaps/${roadmapId}/`,
      );

      setSelectedRoadmap(response.data);
    } catch (err) {
      console.error("Failed to load roadmap:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to load the selected roadmap.",
      );
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadRoadmaps = useCallback(async () => {
    try {
      setError("");
      const response = await api.get("/career/roadmaps/");
      const data = response.data || [];

      setRoadmaps(data);

      if (data.length > 0) {
        loadRoadmap(data[0].id);
        return;
      }

      setSelectedRoadmap(null);

      try {
        const historyResponse = await api.get(
          "/career/history/",
        );
        const history = historyResponse.data || [];

        setAnalyses(history);
        setSelectedAnalysisId(
          history[0]?.id?.toString() || "",
        );
      } catch (historyError) {
        console.error(
          "Failed to load career analysis history:",
          historyError,
        );
        setError(
          historyError.response?.data?.detail ||
            "Unable to load saved career analyses.",
        );
      }
    } catch (err) {
      console.error("Failed to load career roadmaps:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to load career roadmaps.",
      );
    } finally {
      setLoading(false);
    }
  }, [loadRoadmap]);

  const generateRoadmap = async () => {
    if (!selectedAnalysisId) {
      setError("Please select a saved career analysis.");
      return;
    }

    try {
      setGenerating(true);
      setError("");

      const response = await api.post(
        "/career/roadmap/",
        {
          analysis_id: Number(selectedAnalysisId),
          target_role: targetRole.trim(),
        },
      );
      const createdRoadmap = response.data;

      setRoadmaps((current) => [
        createdRoadmap,
        ...current,
      ]);
      setSelectedRoadmap(createdRoadmap);
      setTargetRole("");
    } catch (err) {
      console.error("Failed to generate career roadmap:", err);

      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          "Unable to generate the career roadmap.",
      );
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadRoadmaps();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadRoadmaps]);

  const roadmap = selectedRoadmap?.roadmap;

  if (loading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />

        <main className="dashboard-main career-roadmap-page">
          <div className="career-roadmap-loading">
            <Loader2 className="spin" size={28} />
            <p>Loading your career roadmap...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main career-roadmap-page">
      <div className="career-roadmap-header">
        <button
          className="career-roadmap-back"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft size={18} />
          Dashboard
        </button>

        <div>
          <div className="career-roadmap-title-row">
            <Map size={28} />
            <h1>Career Roadmap</h1>
          </div>

          <p>
            Turn your career analysis into a structured learning
            and project plan.
          </p>
        </div>
      </div>

      {error && (
        <div className="career-roadmap-error">
          {error}
        </div>
      )}

      {roadmaps.length === 0 ? (
        <div className="career-roadmap-empty">
          <Map size={42} />

          {analyses.length > 0 ? (
            <>
              <h2>Create your career roadmap</h2>

              <p>
                You have {analyses.length} saved career{" "}
                {analyses.length === 1
                  ? "analysis"
                  : "analyses"}
                . Choose one to generate a personalized learning
                and project plan.
              </p>

              <form
                className="roadmap-generation-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  generateRoadmap();
                }}
              >
                <label htmlFor="roadmap-analysis">
                  Saved Career Analysis
                </label>

                <select
                  id="roadmap-analysis"
                  value={selectedAnalysisId}
                  onChange={(event) =>
                    setSelectedAnalysisId(event.target.value)
                  }
                  required
                >
                  <option value="" disabled>
                    Select an analysis
                  </option>

                  {analyses.map((analysis) => (
                    <option
                      key={analysis.id}
                      value={analysis.id}
                    >
                      {getAnalysisLabel(analysis)}
                    </option>
                  ))}
                </select>

                <label htmlFor="roadmap-target-role">
                  Target Role <span>Optional</span>
                </label>

                <input
                  id="roadmap-target-role"
                  type="text"
                  value={targetRole}
                  onChange={(event) =>
                    setTargetRole(event.target.value)
                  }
                  placeholder="Leave blank to infer from the analysis"
                />

                <button
                  type="submit"
                  disabled={
                    generating || !selectedAnalysisId
                  }
                >
                  {generating ? (
                    <>
                      <Loader2
                        className="spin"
                        size={17}
                      />
                      Generating Roadmap...
                    </>
                  ) : (
                    <>
                      <Sparkles size={17} />
                      Generate Roadmap
                    </>
                  )}
                </button>
              </form>

              <button
                className="career-roadmap-secondary"
                type="button"
                onClick={() =>
                  navigate("/career-analysis")
                }
              >
                Start New Career Analysis
              </button>
            </>
          ) : (
            <>
              <h2>No career roadmap yet</h2>

              <p>
                Generate a career analysis first, then create a
                personalized roadmap from your skill gaps.
              </p>

              <button
                onClick={() =>
                  navigate("/career-analysis")
                }
              >
                <Sparkles size={17} />
                Start Career Analysis
              </button>
            </>
          )}
        </div>
      ) : (
        <div className="career-roadmap-layout">
          {/* Roadmap history */}
          <aside className="career-roadmap-sidebar">
            <div className="roadmap-sidebar-heading">
              <h3>Your Roadmaps</h3>
              <span>{roadmaps.length}</span>
            </div>

            {roadmaps.map((item) => (
              <button
                key={item.id}
                className={`roadmap-history-item ${
                  selectedRoadmap?.id === item.id
                    ? "active"
                    : ""
                }`}
                onClick={() => loadRoadmap(item.id)}
              >
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.target_role}</small>
                </div>

                <ChevronRight size={17} />
              </button>
            ))}
          </aside>

          {/* Main roadmap */}
          <main className="career-roadmap-content">
            {detailLoading ? (
              <div className="career-roadmap-loading">
                <Loader2 className="spin" size={26} />
                <p>Loading roadmap...</p>
              </div>
            ) : roadmap ? (
              <>
                {/* Overview */}
                <section className="roadmap-overview-card">
                  <div className="roadmap-overview-icon">
                    <Target size={24} />
                  </div>

                  <div>
                    <span className="roadmap-label">
                      Target Role
                    </span>

                    <h2>
                      {roadmap.target_role ||
                        selectedRoadmap.target_role}
                    </h2>

                    <p>{roadmap.summary}</p>
                  </div>
                </section>

                {/* Skills */}
                <section className="roadmap-section">
                  <div className="roadmap-section-heading">
                    <BookOpen size={21} />
                    <div>
                      <h2>Skills to Learn</h2>
                      <p>
                        Skills prioritized from your career
                        analysis.
                      </p>
                    </div>
                  </div>

                  <div className="roadmap-skill-grid">
                    {roadmap.skills_to_learn?.map(
                      (item, index) => (
                        <div
                          className="roadmap-skill-card"
                          key={`${item.skill}-${index}`}
                        >
                          <div className="roadmap-card-top">
                            <h3>{item.skill}</h3>

                            <span
                              className={`priority priority-${(
                                item.priority || ""
                              ).toLowerCase()}`}
                            >
                              {item.priority}
                            </span>
                          </div>

                          <p>{item.reason}</p>
                        </div>
                      ),
                    )}
                  </div>
                </section>

                {/* Learning Topics */}
                <section className="roadmap-section">
                  <div className="roadmap-section-heading">
                    <BookOpen size={21} />
                    <div>
                      <h2>Learning Topics</h2>
                      <p>
                        Topics to study for each identified
                        skill.
                      </p>
                    </div>
                  </div>

                  <div className="roadmap-topic-list">
                    {roadmap.learning_topics?.map(
                      (item, index) => (
                        <div
                          className="roadmap-topic-card"
                          key={`${item.topic}-${index}`}
                        >
                          <div className="topic-number">
                            {index + 1}
                          </div>

                          <div className="topic-content">
                            <div className="topic-heading">
                              <h3>{item.topic}</h3>

                              <span>
                                {item.skill}
                              </span>
                            </div>

                            <p>{item.outcome}</p>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>

                {/* Projects */}
                <section className="roadmap-section">
                  <div className="roadmap-section-heading">
                    <Code2 size={21} />
                    <div>
                      <h2>Recommended Projects</h2>
                      <p>
                        Build projects that demonstrate the
                        skills you're learning.
                      </p>
                    </div>
                  </div>

                  <div className="roadmap-project-grid">
                    {roadmap.recommended_projects?.map(
                      (project, index) => (
                        <div
                          className="roadmap-project-card"
                          key={`${project.name}-${index}`}
                        >
                          <div className="project-icon">
                            <BriefcaseBusiness size={20} />
                          </div>

                          <h3>{project.name}</h3>

                          <p>
                            {project.description}
                          </p>

                          <div className="project-purpose">
                            <strong>Purpose:</strong>{" "}
                            {project.purpose}
                          </div>

                          <div className="project-skills">
                            {project.skills?.map(
                              (skill) => (
                                <span key={skill}>
                                  {skill}
                                </span>
                              ),
                            )}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>

                {/* Phases */}
                <section className="roadmap-section">
                  <div className="roadmap-section-heading">
                    <Map size={21} />
                    <div>
                      <h2>Learning Phases</h2>
                      <p>
                        Follow the roadmap in sequence.
                      </p>
                    </div>
                  </div>

                  <div className="roadmap-phases">
                    {roadmap.phases?.map(
                      (phase, index) => (
                        <div
                          className="roadmap-phase"
                          key={`${phase.phase}-${index}`}
                        >
                          <div className="phase-number">
                            {index + 1}
                          </div>

                          <div className="phase-content">
                            <span className="phase-label">
                              Phase {index + 1}
                            </span>

                            <h3>{phase.phase}</h3>

                            <p>
                              {phase.objective}
                            </p>

                            <div className="phase-block">
                              <strong>Skills</strong>

                              <div>
                                {phase.skills?.map(
                                  (skill) => (
                                    <span key={skill}>
                                      {skill}
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>

                            <div className="phase-block">
                              <strong>Topics</strong>

                              <div>
                                {phase.topics?.map(
                                  (topic) => (
                                    <span key={topic}>
                                      {topic}
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>

                            <div className="phase-block">
                              <strong>Projects</strong>

                              <div>
                                {phase.projects?.map(
                                  (project) => (
                                    <span key={project}>
                                      {project}
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>

                {/* Next steps */}
                <section className="roadmap-next-steps">
                  <div className="roadmap-section-heading">
                    <CheckCircle2 size={21} />

                    <div>
                      <h2>Immediate Next Steps</h2>
                      <p>
                        Start with these actions.
                      </p>
                    </div>
                  </div>

                  <div className="next-step-list">
                    {roadmap.immediate_next_steps?.map(
                      (step, index) => (
                        <div
                          className="next-step"
                          key={index}
                        >
                          <CheckCircle2 size={18} />
                          <span>{step}</span>
                        </div>
                      ),
                    )}
                  </div>
                </section>
              </>
            ) : null}
          </main>
        </div>
      )}
      </main>
    </div>
  );
}

export default CareerRoadmap;