import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, ClipboardCheck, Sparkles } from "lucide-react";

import api from "../services/api";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import PageHeader from "../components/ui/PageHeader";
import Spinner from "../components/ui/Spinner";

import "./InterviewPractice.css";

function InterviewPractice() {
  const location = useLocation();
  const navigate = useNavigate();

  const analysis = location.state?.analysis;

  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!analysis) {
    return (
      <div className="practice-page">
        <PageHeader
          title="Interview Practice"
          description="Practice answering interview questions generated from one of your career analyses."
        />

        <EmptyState
          icon={ClipboardCheck}
          title="No career analysis selected"
          description="Run a career analysis first — its interview questions power this practice mode."
          action={
            <Button variant="primary" onClick={() => navigate("/career-analysis")}>
              Go to Career Analysis
            </Button>
          }
        />
      </div>
    );
  }

  const preparation = analysis.interview_preparation || {};

  const questions = [
    ...(preparation.technical_questions || []),
    ...(preparation.project_questions || []),
    ...(preparation.gap_based_questions || []),
    ...(preparation.behavioral_questions || []),
  ];

  const question = questions[questionIndex];

  const submitAnswer = async () => {
    if (!answer.trim()) return;

    setLoading(true);
    setEvaluation(null);
    setError("");

    try {
      const response = await api.post("/career/interview/evaluate/", {
        analysis_id: analysis.id,
        question: question.question,
        category: question.category,
        difficulty: question.difficulty,
        answer,
      });

      setEvaluation(response.data.evaluation);
    } catch (err) {
      console.error("Interview evaluation failed:", err);
      setError(
        err.response?.data?.error || "Failed to evaluate your answer. Try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const goToQuestion = (nextIndex) => {
    setQuestionIndex(nextIndex);
    setAnswer("");
    setEvaluation(null);
    setError("");
  };

  if (!question) {
    return (
      <div className="practice-page">
        <PageHeader title="Interview Practice" />

        <EmptyState
          icon={Sparkles}
          title="No interview questions available"
          description="This analysis does not include interview questions yet. Re-run the analysis to generate them."
          action={
            <Button variant="secondary" onClick={() => navigate("/career-analysis")}>
              Back to Career Analysis
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="practice-page">
      <PageHeader
        title="Interview Practice"
        description={`Question ${questionIndex + 1} of ${questions.length} from your career analysis.`}
        actions={
          <Badge tone="accent">
            {question.category} · {question.difficulty}
          </Badge>
        }
      />

      <section className="practice-question-card">
        <h2>{question.question}</h2>

        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Type your answer here..."
          rows={8}
          aria-label="Your answer"
        />

        {error && (
          <p className="practice-error" role="alert">
            {error}
          </p>
        )}

        <div className="practice-actions">
          <Button
            variant="primary"
            onClick={submitAnswer}
            disabled={loading || !answer.trim()}
            loading={loading}
          >
            {loading ? "Evaluating..." : "Evaluate Answer"}
          </Button>
        </div>
      </section>

      {loading && (
        <div className="practice-loading">
          <Spinner label="Reviewing your answer..." />
        </div>
      )}

      {evaluation && (
        <section className="practice-evaluation">
          <header className="practice-evaluation-header">
            <h2>Evaluation</h2>
            <span className="practice-score">{evaluation.score}/100</span>
          </header>

          <div className="practice-evaluation-grid">
            {[
              ["Strengths", evaluation.strengths],
              ["Missing Points", evaluation.missing_points],
              ["Improvement Suggestions", evaluation.improvement_suggestions],
              ["Ideal Answer Points", evaluation.ideal_answer_points],
            ].map(([heading, items]) =>
              items?.length ? (
                <div className="practice-evaluation-block" key={heading}>
                  <h3>{heading}</h3>
                  <ul>
                    {items.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null
            )}
          </div>
        </section>
      )}

      <nav className="practice-nav" aria-label="Question navigation">
        <Button
          variant="secondary"
          onClick={() => goToQuestion(questionIndex - 1)}
          disabled={questionIndex === 0}
        >
          <ArrowLeft size={16} />
          Previous
        </Button>

        <Button
          variant="secondary"
          onClick={() => goToQuestion(questionIndex + 1)}
          disabled={questionIndex === questions.length - 1}
        >
          Next Question
          <ArrowRight size={16} />
        </Button>
      </nav>
    </div>
  );
}

export default InterviewPractice;
