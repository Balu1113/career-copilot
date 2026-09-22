import { useEffect, useState } from "react";
import { Bot, FileText, Send, User } from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./ResumeChat.css";

function ResumeChat() {
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadResumes = async () => {
      try {
        const response = await api.get("/resumes/");

        setResumes(response.data);

        if (response.data.length > 0) {
          setResumeId(String(response.data[0].id));
        }
      } catch (err) {
        setError("Unable to load your resumes.");
      } finally {
        setLoadingResumes(false);
      }
    };

    loadResumes();
  }, []);

  const askQuestion = async (event) => {
    event.preventDefault();

    if (!resumeId) {
      setError("Please select a resume.");
      return;
    }

    if (!question.trim()) {
      return;
    }

    const currentQuestion = question.trim();

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: currentQuestion,
      },
    ]);

    setQuestion("");
    setError("");
    setAsking(true);

    try {
      const response = await api.post("/rag/ask/", {
        resume_id: Number(resumeId),
        question: currentQuestion,
      });

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: response.data.answer,
        },
      ]);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          "Unable to answer your question."
      );
    } finally {
      setAsking(false);
    }
  };

  const selectedResume = resumes.find(
    (resume) => String(resume.id) === String(resumeId)
  );

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main resume-chat-page">
        <div className="resume-chat-header">
          <div>
            <div className="resume-chat-title">
              <Bot size={25} />
              <h1>Resume AI Chat</h1>
            </div>

            <p>
              Ask questions about your resume and get
              answers using RAG.
            </p>
          </div>

          <div className="resume-selector">
            <FileText size={17} />

            <select
              value={resumeId}
              onChange={(event) => {
                setResumeId(event.target.value);
                setMessages([]);
              }}
              disabled={loadingResumes}
            >
              {resumes.length === 0 ? (
                <option value="">
                  No resumes available
                </option>
              ) : (
                resumes.map((resume) => (
                  <option
                    key={resume.id}
                    value={resume.id}
                  >
                    {resume.title}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {error && (
          <div className="resume-chat-error">
            {error}
          </div>
        )}

        <div className="resume-chat-container">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <div className="chat-empty-icon">
                  <Bot size={30} />
                </div>

                <h2>
                  Ask your resume anything
                </h2>

                <p>
                  I can answer questions using the
                  information contained in your uploaded
                  resume.
                </p>

                <div className="suggested-questions">
                  <button
                    onClick={() =>
                      setQuestion(
                        "What are my main technical skills?"
                      )
                    }
                  >
                    What are my main technical skills?
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "What projects are mentioned in my resume?"
                      )
                    }
                  >
                    What projects are mentioned?
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "Summarize my professional experience."
                      )
                    }
                  >
                    Summarize my experience.
                  </button>

                  <button
                    onClick={() =>
                      setQuestion(
                        "What technologies have I worked with?"
                      )
                    }
                  >
                    What technologies have I used?
                  </button>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  className={`chat-message ${
                    message.role === "user"
                      ? "user-message"
                      : "assistant-message"
                  }`}
                  key={index}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? (
                      <User size={17} />
                    ) : (
                      <Bot size={17} />
                    )}
                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>
                </div>
              ))
            )}

            {asking && (
              <div className="chat-message assistant-message">
                <div className="message-avatar">
                  <Bot size={17} />
                </div>

                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
          </div>

          <form
            className="chat-input-area"
            onSubmit={askQuestion}
          >
            <input
              type="text"
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder={
                selectedResume
                  ? `Ask about ${selectedResume.title}...`
                  : "Ask a question about your resume..."
              }
              disabled={asking || resumes.length === 0}
            />

            <button
              type="submit"
              disabled={
                asking ||
                !question.trim() ||
                resumes.length === 0
              }
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default ResumeChat;