import { useCallback, useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Bot,
  GraduationCap,
  Plus,
  Send,
  Trash2,
  User,
} from "lucide-react";
import api from "../services/api";
import TutorBlocks, { TutorSuggestions } from "../components/TutorBlocks";
import "../components/ChatShell.css";
import "./LearnChat.css";

const LEVEL_OPTIONS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const STARTER_TOPICS = [
  "Teach me Python decorators",
  "Explain SQL joins with examples",
  "I want to learn React hooks",
  "What is Docker and how do I use it?",
  "Teach me git for team projects",
  "Explain time complexity with examples",
];

function LearnChat() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [level, setLevel] = useState("beginner");
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [creating, setCreating] = useState(false);
  const [opening, setOpening] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const response = await api.get("/learn/sessions/");
        setSessions(Array.isArray(response.data) ? response.data : []);
      } catch {
        setError("Unable to load your learning chats.");
      } finally {
        setLoadingSessions(false);
      }
    };

    loadSessions();
  }, []);

  useEffect(() => {
    const node = messagesRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [messages, sending]);

  const createSession = useCallback(async (chosenLevel) => {
    setCreating(true);
    setError("");

    try {
      const response = await api.post("/learn/sessions/", {
        level: chosenLevel || level,
      });

      const session = response.data;

      setSessions((previous) => [session, ...previous]);
      setActiveSession(session);
      setMessages([]);
      return session;
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to start a new learning chat."
      );
      return null;
    } finally {
      setCreating(false);
    }
  }, [level]);

  const openSession = async (session) => {
    setError("");
    setOpening(true);

    try {
      const response = await api.get(
        `/learn/sessions/${session.id}/`
      );

      setActiveSession(response.data);
      setMessages(response.data.messages || []);
      setLevel(response.data.level);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to open that chat."
      );
    } finally {
      setOpening(false);
    }
  };

  const deleteSession = async (sessionId) => {
    setError("");

    try {
      await api.delete(`/learn/sessions/${sessionId}/`);

      setSessions((previous) =>
        previous.filter((session) => session.id !== sessionId)
      );

      if (activeSession && activeSession.id === sessionId) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to delete that chat."
      );
    }
  };

  const sendMessage = async (rawText) => {
    const text = String(rawText || "").trim();

    if (!text || sending || opening || creating) {
      return;
    }

    let session = activeSession;

    if (!session) {
      session = await createSession(level);
      if (!session) return;
    }

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);
    setInput("");
    setError("");
    setSending(true);

    try {
      const response = await api.post(
        `/learn/sessions/${session.id}/messages/`,
        { content: text }
      );

      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: response.data.reply },
      ]);

      const updated = response.data.session;

      if (updated) {
        setActiveSession((previous) =>
          previous && previous.id === updated.id
            ? { ...previous, ...updated }
            : previous
        );

        setSessions((previous) =>
          previous.map((item) =>
            item.id === updated.id
              ? { ...item, ...updated }
              : item
          )
        );
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "The tutor could not answer that. Try again."
      );
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(input);
  };

  const lastAssistantIndex = (() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index].role === "assistant") {
        return index;
      }
    }
    return -1;
  })();

  return (
    <main className="dashboard-main learn-page">
      <div className="learn-header">
        <div>
          <div className="learn-title">
            <GraduationCap size={25} />
            <h1>Learning Tutor</h1>
          </div>

          <p>
            Tell me what you want to learn and I will teach
            you step by step, with examples.
          </p>
        </div>

        <div className="learn-header-actions">
          <div
            className="learn-level-picker"
            role="group"
            aria-label="Learning level"
            title={
              activeSession
                ? "Level applies to new chats"
                : "Choose your level for new chats"
            }
          >
            {LEVEL_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={
                  level === option.value
                    ? "level-option active"
                    : "level-option"
                }
                onClick={() => setLevel(option.value)}
                disabled={Boolean(activeSession)}
              >
                {option.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="learn-new-chat"
            onClick={() => createSession()}
            disabled={creating}
          >
            <Plus size={15} />
            New chat
          </button>
        </div>
      </div>

      {error && <div className="learn-error">{error}</div>}

      <div className="learn-container">
        <aside className="learn-sidebar">
          <div className="learn-sidebar-title">Chats</div>

          <div className="learn-session-list">
            {loadingSessions ? (
              <div className="learn-session-empty">
                Loading...
              </div>
            ) : sessions.length === 0 ? (
              <div className="learn-session-empty">
                No chats yet.
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className={`learn-session ${
                    activeSession &&
                    activeSession.id === session.id
                      ? "active-session"
                      : ""
                  }`}
                >
                  <button
                    type="button"
                    className="learn-session-open"
                    onClick={() => openSession(session)}
                  >
                    <BookOpen size={14} />

                    <span className="learn-session-text">
                      <span className="learn-session-name">
                        {session.title || "New chat"}
                      </span>

                      <span className="learn-session-meta">
                        {session.message_count || 0} messages
                        {" · "}
                        {session.level || "beginner"}
                      </span>
                    </span>
                  </button>

                  <button
                    type="button"
                    className="learn-session-delete"
                    title="Delete chat"
                    onClick={() => deleteSession(session.id)}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>

        <section className="learn-conversation">
          <div className="chat-messages" ref={messagesRef}>
            {messages.length === 0 ? (
              <div className="chat-empty">
                <div className="chat-empty-icon">
                  <GraduationCap size={30} />
                </div>

                <h2>What do you want to learn today?</h2>

                <p>
                  Ask about any skill — programming,
                  databases, tools — and I will teach it
                  with explanations, code examples, and
                  practice questions.
                </p>

                <div className="suggested-questions">
                  {STARTER_TOPICS.map((topic) => (
                    <button
                      key={topic}
                      onClick={() => sendMessage(topic)}
                      disabled={sending || creating || opening}
                    >
                      {topic}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => {
                const isLastSuggestionSource =
                  index === lastAssistantIndex;

                return (
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
                      {message.role === "user" ? (
                        message.content
                      ) : (
                        <>
                          <TutorBlocks
                            content={message.content}
                          />

                          {isLastSuggestionSource && (
                            <TutorSuggestions
                              suggestions={
                                message.content
                                  ?.suggested_questions || []
                              }
                              onPick={sendMessage}
                            />
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {sending && messages.length > 0 && (
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

          <form className="chat-input-area" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="e.g. Teach me Python decorators..."
              disabled={sending || creating || opening}
            />

            <button
              type="submit"
              disabled={
                sending ||
                creating ||
                opening ||
                !input.trim()
              }
            >
              <Send size={18} />
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}

export default LearnChat;
