import {
  BookOpen,
  CheckCircle2,
  CircleHelp,
  Clock3,
  Compass,
  Lightbulb,
  ListChecks,
  Target,
  Terminal,
  TriangleAlert,
} from "lucide-react";
import "./LessonContent.css";

function LessonContent({ lesson, eyebrow }) {
  if (!lesson) return null;

  const sections = lesson.sections || [];
  const objectives = lesson.learning_objectives || [];
  const prerequisites = lesson.prerequisites || [];
  const concepts = lesson.key_concepts || [];
  const mistakes = lesson.common_mistakes || [];
  const exercises = lesson.practice_exercises || [];
  const questions = lesson.assessment_questions || [];
  const checklist = lesson.mastery_checklist || [];
  const nextSteps = lesson.next_steps || [];

  return (
    <div className="lesson-content">
      <section className="lesson-detail-overview">
        <div>
          <span className="lesson-content-eyebrow">
            {eyebrow || "Your lesson"}
          </span>
          <h2>{lesson.title}</h2>
          <p>{lesson.overview}</p>
        </div>

        <span className="lesson-detail-time">
          <Clock3 size={16} />
          {lesson.estimated_time || "Self-paced"}
        </span>
      </section>

      {objectives.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Target size={20} />
            <h2>What you will be able to do</h2>
          </div>
          <ul className="lesson-detail-list lesson-detail-list--plain">
            {objectives.map((objective, index) => (
              <li key={`${index}-${objective}`}>{objective}</li>
            ))}
          </ul>
        </section>
      )}

      {prerequisites.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Compass size={20} />
            <h2>Before you start</h2>
          </div>
          <ul className="lesson-detail-list lesson-detail-list--plain">
            {prerequisites.map((prerequisite, index) => (
              <li key={`${index}-${prerequisite}`}>
                {prerequisite}
              </li>
            ))}
          </ul>
        </section>
      )}

      {concepts.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Lightbulb size={20} />
            <h2>Key concepts</h2>
          </div>
          <ul className="lesson-detail-list lesson-detail-list--concepts">
            {concepts.map((concept, index) => (
              <li key={`${index}-${concept}`}>{concept}</li>
            ))}
          </ul>
        </section>
      )}

      {sections.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <BookOpen size={20} />
            <h2>In depth</h2>
          </div>

          <div className="lesson-deep-dives">
            {sections.map((part, index) => (
              <article
                className="lesson-deep-dive"
                key={`${index}-${part.heading}`}
              >
                <div className="lesson-deep-dive-heading">
                  <span>{index + 1}</span>
                  <h3>{part.heading}</h3>
                </div>
                <p>{part.content}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {lesson.walkthrough && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Terminal size={20} />
            <h2>Hands-on walkthrough</h2>
          </div>
          <p className="lesson-detail-prose">
            {lesson.walkthrough}
          </p>
        </section>
      )}

      {lesson.example && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Target size={20} />
            <h2>Worked example</h2>
          </div>
          <p className="lesson-detail-prose lesson-detail-prose--code">
            {lesson.example}
          </p>
        </section>
      )}

      {mistakes.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <TriangleAlert size={20} />
            <h2>Common mistakes to avoid</h2>
          </div>
          <ul className="lesson-detail-list">
            {mistakes.map((mistake, index) => (
              <li key={`${index}-${mistake}`}>{mistake}</li>
            ))}
          </ul>
        </section>
      )}

      {exercises.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <CheckCircle2 size={20} />
            <h2>Practice exercises</h2>
          </div>
          <ol className="lesson-detail-list lesson-detail-list--ordered">
            {exercises.map((exercise, index) => (
              <li key={`${index}-${exercise}`}>{exercise}</li>
            ))}
          </ol>
        </section>
      )}

      {lesson.project_challenge && (
        <section className="lesson-project-challenge">
          <div className="lesson-detail-heading">
            <Terminal size={20} />
            <h2>End-to-end project challenge</h2>
          </div>
          <p>{lesson.project_challenge}</p>
        </section>
      )}

      {questions.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <CircleHelp size={20} />
            <h2>Test yourself</h2>
          </div>
          <ol className="lesson-detail-list lesson-detail-list--ordered">
            {questions.map((question, index) => (
              <li key={`${index}-${question}`}>{question}</li>
            ))}
          </ol>
        </section>
      )}

      {lesson.checkpoint && (
        <section className="lesson-detail-checkpoint">
          <strong>Check your understanding</strong>
          <p>{lesson.checkpoint}</p>
        </section>
      )}

      {checklist.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <ListChecks size={20} />
            <h2>Mastery checklist</h2>
          </div>
          <ul className="lesson-detail-list lesson-detail-list--checklist">
            {checklist.map((entry, index) => (
              <li key={`${index}-${entry}`}>{entry}</li>
            ))}
          </ul>
        </section>
      )}

      {nextSteps.length > 0 && (
        <section className="lesson-detail-section">
          <div className="lesson-detail-heading">
            <Compass size={20} />
            <h2>What to do next</h2>
          </div>
          <ul className="lesson-detail-list">
            {nextSteps.map((step, index) => (
              <li key={`${index}-${step}`}>{step}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default LessonContent;
