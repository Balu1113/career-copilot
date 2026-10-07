import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  GraduationCap,
  Loader2,
  RefreshCw,
} from "lucide-react";
import api from "../services/api";
import LessonContent from "../components/LessonContent";
import "./CareerRoadmapTutor.css";

const roadmapCollection = {
  skill: "skills_to_learn",
  topic: "learning_topics",
  project: "recommended_projects",
  phase: "phases",
};

const itemTitle = {
  skill: (item) => item.skill,
  topic: (item) => item.topic,
  project: (item) => item.name,
  phase: (item) => item.phase,
};

function CareerRoadmapTutor() {
  const navigate = useNavigate();
  const { roadmapId, contentType, itemIndex } = useParams();
  const [lesson, setLesson] = useState(null);
  const [roadmapTitle, setRoadmapTitle] = useState("");
  const [selectedTitle, setSelectedTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const loadLesson = async () => {
      setLoading(true);
      setLesson(null);
      setError("");
      setRoadmapTitle("");
      setSelectedTitle("");

      const collection = roadmapCollection[contentType];
      const getTitle = itemTitle[contentType];
      const index = Number(itemIndex);

      if (!collection || !getTitle || !Number.isInteger(index) || index < 0) {
        setError("This tutor lesson could not be found.");
        setLoading(false);
        return;
      }

      try {
        const roadmapResponse = await api.get(
          `/career/roadmaps/${roadmapId}/`,
          { signal: controller.signal },
        );
        const roadmapData = roadmapResponse.data.roadmap || {};
        const selectedItem = roadmapData[collection]?.[index];

        if (!selectedItem) {
          setError("This item is no longer available in the selected roadmap.");
          return;
        }

        setRoadmapTitle(roadmapResponse.data.title);
        setSelectedTitle(getTitle(selectedItem));

        const lessonResponse = await api.post(
          `/career/roadmaps/${roadmapId}/tutor/`,
          { content_type: contentType, item_index: index },
          { signal: controller.signal },
        );
        setLesson(lessonResponse.data);
      } catch (requestError) {
        if (controller.signal.aborted) return;
        console.error("Failed to generate roadmap tutor lesson:", requestError);
        setError(
          requestError.response?.data?.detail ||
            "Unable to generate the tutor lesson. Please try again.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };

    loadLesson();
    return () => controller.abort();
  }, [roadmapId, contentType, itemIndex, requestVersion]);

  return (
    <main className="dashboard-main roadmap-tutor-page">
      <header className="roadmap-tutor-header">
        <button
          className="roadmap-tutor-back"
          type="button"
          onClick={() => navigate("/career-roadmap")}
        >
          <ArrowLeft size={17} />
          Back to roadmap
        </button>
        <div className="roadmap-tutor-title">
          <span className="roadmap-tutor-title-icon">
            <GraduationCap size={23} />
          </span>
          <div>
            <span className="roadmap-tutor-eyebrow">AI Career Tutor</span>
            <h1>{selectedTitle || "Your learning lesson"}</h1>
            <p>{roadmapTitle || "Personalized to your career roadmap"}</p>
          </div>
        </div>
      </header>

      {error && (
        <div className="roadmap-tutor-error" role="alert">
          <p>{error}</p>
          {!loading && (
            <button
              type="button"
              onClick={() => setRequestVersion((version) => version + 1)}
            >
              <RefreshCw size={15} />
              Try again
            </button>
          )}
        </div>
      )}

      {loading ? (
        <section className="roadmap-tutor-loading" role="status">
          <Loader2 className="spin" size={30} />
          <h2>Your tutor is preparing a lesson</h2>
          <p>Building an explanation and practice exercises for this roadmap item.</p>
        </section>
      ) : lesson ? (
        <LessonContent lesson={lesson} />
      ) : null}
    </main>
  );
}

export default CareerRoadmapTutor;
