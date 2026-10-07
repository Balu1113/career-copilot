import { useCallback, useEffect, useState } from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Clock3,
  GraduationCap,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import api from "../services/api";
import LessonContent from "../components/LessonContent";
import "./CareerRoadmapLessons.css";

const LEVELS = ["beginner", "intermediate", "advanced"];

const levelLabel = (level) =>
  level ? level.charAt(0).toUpperCase() + level.slice(1) : "";

function CareerRoadmapLessons() {
  const navigate = useNavigate();
  const { roadmapId } = useParams();

  const [roadmap, setRoadmap] = useState(null);
  const [learnerLevel, setLearnerLevel] = useState("beginner");
  const [lessons, setLessons] = useState([]);
  const [progress, setProgress] = useState({
    total: 0,
    completed: 0,
  });
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [selectedLevel, setSelectedLevel] =
    useState("beginner");
  const [filterLevel, setFilterLevel] = useState("all");
  const [error, setError] = useState("");

  const [openLessonId, setOpenLessonId] = useState(null);
  const [lessonDetail, setLessonDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

  const loadPlan = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        `/career/roadmaps/${roadmapId}/lessons/`,
      );
      const data = response.data;

      setRoadmap(data.roadmap);
      setLearnerLevel(data.learner_level || "beginner");
      setLessons(data.lessons || []);
      setProgress(data.progress || { total: 0, completed: 0 });
    } catch (requestError) {
      console.error("Failed to load lesson plan:", requestError);
      setError(
        requestError.response?.data?.detail ||
          "Unable to load the lesson plan.",
      );
    } finally {
      setLoading(false);
    }
  }, [roadmapId]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      loadPlan();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadPlan]);

  const createPlan = async (regenerate = false) => {
    try {
      setCreating(true);
      setError("");

      const response = await api.post(
        `/career/roadmaps/${roadmapId}/lessons/`,
        { level: selectedLevel, regenerate },
      );
      const data = response.data;

      setRoadmap(data.roadmap);
      setLearnerLevel(data.learner_level || selectedLevel);
      setLessons(data.lessons || []);
      setProgress(data.progress || { total: 0, completed: 0 });
      setFilterLevel("all");
    } catch (requestError) {
      console.error("Failed to generate lesson plan:", requestError);
      setError(
        requestError.response?.data?.detail ||
          "Unable to generate the lesson plan.",
      );
    } finally {
      setCreating(false);
    }
  };

  const regeneratePlan = async () => {
    const confirmed = window.confirm(
      "Regenerate the lesson plan? Your progress on the current lessons will be reset.",
    );

    if (!confirmed) return;

    setSelectedLevel(learnerLevel);
    await createPlan(true);
  };

  const openLesson = async (lesson) => {
    setOpenLessonId(lesson.id);
    setLessonDetail(null);
    setDetailError("");

    try {
      setDetailLoading(true);

      const response = await api.get(
        `/career/roadmaps/${roadmapId}/lessons/${lesson.id}/`,
      );

      setLessonDetail(response.data);
      setLessons((current) =>
        current.map((item) =>
          item.id === response.data.id
            ? { ...item, ...response.data }
            : item,
        ),
      );
    } catch (requestError) {
      console.error("Failed to load lesson:", requestError);
      setDetailError(
        requestError.response?.data?.detail ||
          "Unable to open this lesson. Please try again.",
      );
    } finally {
      setDetailLoading(false);
    }
  };

  const closeLesson = () => {
    setOpenLessonId(null);
    setLessonDetail(null);
    setDetailError("");
  };

  const toggleComplete = async (lesson) => {
    try {
      setUpdatingId(lesson.id);
      setDetailError("");

      const response = await api.patch(
        `/career/roadmaps/${roadmapId}/lessons/${lesson.id}/`,
        { completed: !lesson.completed },
      );

      const updated = response.data;

      setLessons((current) =>
        current.map((item) =>
          item.id === updated.id
            ? { ...item, ...updated }
            : item,
        ),
      );

      setProgress((current) => ({
        total: current.total,
        completed: current.completed +
          (updated.completed && !lesson.completed ? 1 : 0) -
          (!updated.completed && lesson.completed ? 1 : 0),
      }));

      if (openLessonId === updated.id) {
        setLessonDetail((current) =>
          current ? { ...current, ...updated } : current,
        );
      }
    } catch (requestError) {
      console.error("Failed to update lesson:", requestError);
      setDetailError(
        requestError.response?.data?.detail ||
          "Unable to update this lesson.",
      );
    } finally {
      setUpdatingId(null);
    }
  };

  const visibleLessons =
    filterLevel === "all"
      ? lessons
      : lessons.filter((lesson) => lesson.level === filterLevel);

  const nextLesson =
    lessons.find((lesson) => !lesson.completed) || null;

  const activeLevels = LEVELS.filter((level) =>
    lessons.some((lesson) => lesson.level === level),
  );

  const openLessonRecord =
    lessons.find((lesson) => lesson.id === openLessonId) ||
    null;

  const nextAfterOpen =
    lessons.find(
      (lesson) =>
        lesson.position > (openLessonRecord?.position ?? -1) &&
        !lesson.completed,
    ) || null;

  if (loading) {
    return (
      <main className="dashboard-main lesson-plan-page">
        <div className="lesson-plan-status">
          <Loader2 className="spin" size={28} />
          <p>Loading your lesson plan...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="dashboard-main lesson-plan-page">
      <header className="lesson-plan-header">
        <button
          className="lesson-plan-back"
          type="button"
          onClick={() => navigate("/career-roadmap")}
        >
          <ArrowLeft size={17} />
          Back to roadmap
        </button>

        <div className="lesson-plan-title">
          <span className="lesson-plan-title-icon">
            <GraduationCap size={23} />
          </span>
          <div>
            <span className="lesson-plan-eyebrow">
              AI Career Tutor
            </span>
            <h1>Roadmap Lesson Plan</h1>
            <p>
              {roadmap
                ? `${roadmap.title} · ${levelLabel(learnerLevel)} track`
                : "Personalized to your career roadmap"}
            </p>
          </div>
        </div>
      </header>

      {error && (
        <div className="lesson-plan-error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={loadPlan}>
            <RefreshCw size={15} />
            Try again
          </button>
        </div>
      )}

      {openLessonId ? (
        <section className="lesson-view">
          <div className="lesson-view-toolbar">
            <button
              type="button"
              onClick={closeLesson}
              disabled={detailLoading}
            >
              <ArrowLeft size={16} />
              Back to plan
            </button>

            {openLessonRecord && (
              <span
                className={`lesson-level-badge level-${openLessonRecord.level}`}
              >
                {levelLabel(openLessonRecord.level)}
              </span>
            )}
          </div>

          {detailLoading ? (
            <div className="lesson-plan-status" role="status">
              <Loader2 className="spin" size={30} />
              <h2>Your tutor is writing this lesson</h2>
              <p>
                Building explanations, examples, and practice
                exercises for this roadmap item.
              </p>
            </div>
          ) : detailError ? (
            <div className="lesson-plan-error" role="alert">
              <p>{detailError}</p>
              {openLessonRecord && (
                <button
                  type="button"
                  onClick={() => openLesson(openLessonRecord)}
                >
                  <RefreshCw size={15} />
                  Try again
                </button>
              )}
            </div>
          ) : lessonDetail ? (
            <>
              <LessonContent
                lesson={lessonDetail.lesson || lessonDetail}
                eyebrow={`Lesson ${lessonDetail.position + 1}`}
              />

              <div className="lesson-detail-actions">
                <button
                  className="lesson-complete-btn"
                  type="button"
                  onClick={() =>
                    toggleComplete(lessonDetail)
                  }
                  disabled={updatingId === lessonDetail.id}
                >
                  {updatingId === lessonDetail.id ? (
                    <Loader2 className="spin" size={16} />
                  ) : (
                    <CheckCircle2 size={16} />
                  )}
                  {lessonDetail.completed
                    ? "Mark as not completed"
                    : "Mark as complete"}
                </button>

                {nextAfterOpen && (
                  <button
                    className="lesson-next-btn"
                    type="button"
                    onClick={() => openLesson(nextAfterOpen)}
                  >
                    Next lesson
                    <ArrowRight size={16} />
                  </button>
                )}
              </div>
            </>
          ) : null}
        </section>
      ) : lessons.length === 0 ? (
        <section className="lesson-plan-create">
          <Sparkles size={38} />
          <h2>Generate your lesson plan</h2>
          <p>
            Turn every skill, topic, project, and phase in this
            roadmap into an ordered lesson you can work through
            with your AI tutor.
          </p>

          <label htmlFor="lesson-level">
            Starting level
          </label>

          <select
            id="lesson-level"
            value={selectedLevel}
            onChange={(event) =>
              setSelectedLevel(event.target.value)
            }
            disabled={creating}
          >
            {LEVELS.map((level) => (
              <option key={level} value={level}>
                {levelLabel(level)}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => createPlan(false)}
            disabled={creating}
          >
            {creating ? (
              <>
                <Loader2 className="spin" size={17} />
                Generating lesson plan...
              </>
            ) : (
              <>
                <Sparkles size={17} />
                Generate Lesson Plan
              </>
            )}
          </button>
        </section>
      ) : (
        <>
          <section className="lesson-plan-progress">
            <div className="lesson-progress-info">
              <strong>
                {progress.completed} of {progress.total}{" "}
                lessons completed
              </strong>

              <div className="lesson-progress-track">
                <span
                  style={{
                    width: `${
                      progress.total
                        ? (progress.completed /
                            progress.total) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div className="lesson-plan-actions">
              {nextLesson && (
                <button
                  type="button"
                  onClick={() => openLesson(nextLesson)}
                >
                  <GraduationCap size={16} />
                  {progress.completed > 0
                    ? "Continue learning"
                    : "Start learning"}
                </button>
              )}

              <button
                className="lesson-plan-regenerate"
                type="button"
                onClick={regeneratePlan}
                disabled={creating}
              >
                {creating ? (
                  <Loader2 className="spin" size={16} />
                ) : (
                  <RefreshCw size={16} />
                )}
                Regenerate
              </button>
            </div>
          </section>

          <div className="lesson-level-filters">
            <button
              type="button"
              className={
                filterLevel === "all" ? "active" : ""
              }
              onClick={() => setFilterLevel("all")}
            >
              All levels
            </button>

            {activeLevels.map((level) => (
              <button
                key={level}
                type="button"
                className={
                  filterLevel === level ? "active" : ""
                }
                onClick={() => setFilterLevel(level)}
              >
                {levelLabel(level)}
              </button>
            ))}
          </div>

          <ol className="lesson-plan-list">
            {visibleLessons.map((lesson) => (
              <li key={lesson.id}>
                <button
                  type="button"
                  className={`lesson-plan-item ${
                    lesson.completed ? "completed" : ""
                  }`}
                  onClick={() => openLesson(lesson)}
                >
                  <span className="lesson-item-number">
                    {lesson.completed ? (
                      <CheckCircle2 size={17} />
                    ) : (
                      lesson.position + 1
                    )}
                  </span>

                  <span className="lesson-item-body">
                    <span className="lesson-item-heading">
                      <strong>{lesson.title}</strong>
                      <span
                        className={`lesson-level-badge level-${lesson.level}`}
                      >
                        {levelLabel(lesson.level)}
                      </span>
                    </span>

                    <small>{lesson.overview}</small>

                    <span className="lesson-item-meta">
                      <Clock3 size={14} />
                      {lesson.estimated_time || "Self-paced"}
                      <span>
                        · {levelLabel(lesson.content_type)}
                      </span>
                    </span>
                  </span>

                  <ChevronRight size={17} />
                </button>
              </li>
            ))}
          </ol>

          {visibleLessons.length === 0 && (
            <p className="lesson-plan-empty-filter">
              No {filterLevel} lessons in this plan yet.
            </p>
          )}
        </>
      )}
    </main>
  );
}

export default CareerRoadmapLessons;
