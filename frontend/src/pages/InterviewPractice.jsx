import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api";

export default function InterviewPractice() {
  const location = useLocation();
  const navigate = useNavigate();

  const analysis = location.state?.analysis;

  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!analysis) {
    return (
      <div style={{ padding: "40px" }}>
        <h2>Interview Practice</h2>
        <p>
          No career analysis was selected.
        </p>

        <button onClick={() => navigate("/career")}>
          Back to Career Analysis
        </button>
      </div>
    );
  }

  const preparation =
    analysis.interview_preparation || {};

  const questions = [
    ...(preparation.technical_questions || []),
    ...(preparation.project_questions || []),
    ...(preparation.gap_based_questions || []),
    ...(preparation.behavioral_questions || []),
  ];

  const question = questions[questionIndex];

  const submitAnswer = async () => {
    if (!answer.trim()) {
      return;
    }

    setLoading(true);
    setEvaluation(null);

    try {
      const token = localStorage.getItem("access_token");

      const response = await axios.post(
        `${API_BASE_URL}/career/interview/evaluate/`,
        {
          analysis_id: analysis.id,
          question: question.question,
          category: question.category,
          difficulty: question.difficulty,
          answer: answer,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setEvaluation(response.data.evaluation);
    } catch (error) {
      console.error(
        "Interview evaluation failed:",
        error
      );

      alert(
        error.response?.data?.error ||
        "Failed to evaluate answer."
      );
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    if (questionIndex < questions.length - 1) {
      setQuestionIndex(
        questionIndex + 1
      );

      setAnswer("");
      setEvaluation(null);
    }
  };

  const previousQuestion = () => {
    if (questionIndex > 0) {
      setQuestionIndex(
        questionIndex - 1
      );

      setAnswer("");
      setEvaluation(null);
    }
  };

  if (!question) {
    return (
      <div style={{ padding: "40px" }}>
        <h2>Interview Practice</h2>
        <p>
          No interview questions are available
          for this analysis.
        </p>
      </div>
    );
  }

  return (
    <div
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "40px 20px",
      }}
    >
      <h1>Interview Practice</h1>

      <p>
        Question {questionIndex + 1} of{" "}
        {questions.length}
      </p>

      <div
        style={{
          padding: "24px",
          border: "1px solid #ddd",
          borderRadius: "12px",
          marginTop: "20px",
        }}
      >
        <div>
          <strong>
            {question.category}
          </strong>

          {" • "}

          <strong>
            {question.difficulty}
          </strong>
        </div>

        <h2 style={{ marginTop: "20px" }}>
          {question.question}
        </h2>

        <textarea
          value={answer}
          onChange={(e) =>
            setAnswer(e.target.value)
          }
          placeholder="Type your answer here..."
          rows={8}
          style={{
            width: "100%",
            marginTop: "20px",
            padding: "12px",
            resize: "vertical",
            boxSizing: "border-box",
          }}
        />

        <button
          onClick={submitAnswer}
          disabled={
            loading ||
            !answer.trim()
          }
          style={{
            marginTop: "15px",
            padding: "12px 20px",
            cursor: "pointer",
          }}
        >
          {loading
            ? "Evaluating..."
            : "Evaluate Answer"}
        </button>
      </div>

      {evaluation && (
        <div
          style={{
            marginTop: "30px",
            padding: "24px",
            border: "1px solid #ddd",
            borderRadius: "12px",
          }}
        >
          <h2>
            Score: {evaluation.score}/100
          </h2>

          <section>
            <h3>Strengths</h3>

            <ul>
              {evaluation.strengths?.map(
                (item, index) => (
                  <li key={index}>
                    {item}
                  </li>
                )
              )}
            </ul>
          </section>

          <section>
            <h3>Missing Points</h3>

            <ul>
              {evaluation.missing_points?.map(
                (item, index) => (
                  <li key={index}>
                    {item}
                  </li>
                )
              )}
            </ul>
          </section>

          <section>
            <h3>Improvement Suggestions</h3>

            <ul>
              {evaluation.improvement_suggestions?.map(
                (item, index) => (
                  <li key={index}>
                    {item}
                  </li>
                )
              )}
            </ul>
          </section>

          <section>
            <h3>Ideal Answer Points</h3>

            <ul>
              {evaluation.ideal_answer_points?.map(
                (item, index) => (
                  <li key={index}>
                    {item}
                  </li>
                )
              )}
            </ul>
          </section>
        </div>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "25px",
        }}
      >
        <button
          onClick={previousQuestion}
          disabled={questionIndex === 0}
        >
          Previous
        </button>

        <button
          onClick={nextQuestion}
          disabled={
            questionIndex ===
            questions.length - 1
          }
        >
          Next Question
        </button>
      </div>
    </div>
  );
}