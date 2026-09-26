import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  Download,
  FileText,
  Loader2,
  Pencil,
  Sparkles,
  Trash2,
} from "lucide-react";

import api from "../services/api";

import "./Resumes.css";

function Resumes() {
  const navigate = useNavigate();

  const [uploadedResumes, setUploadedResumes] = useState([]);
  const [generatedResumes, setGeneratedResumes] = useState([]);

  const [activeResumeId, setActiveResumeId] = useState(null);
  const [activeTab, setActiveTab] = useState("uploaded");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [actingResumeId, setActingResumeId] = useState(null);

  const fetchResumes = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }

      setError("");

      const [uploadedResponse, generatedResponse] = await Promise.all([
        api.get("/resumes/"),
        api.get("/resume-builder/resumes/"),
      ]);

      setUploadedResumes(
        Array.isArray(uploadedResponse.data)
          ? uploadedResponse.data
          : [],
      );

      setGeneratedResumes(
        Array.isArray(generatedResponse.data)
          ? generatedResponse.data
          : [],
      );
    } catch (err) {
      console.error(err);

      setError("Unable to load resumes.");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const runAction = async (resumeId, action) => {
    setActingResumeId(resumeId);
    setError("");

    try {
      await action();
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          err?.response?.data?.error ||
          "Unable to perform this action.",
      );
    } finally {
      setActingResumeId(null);
    }
  };

  const activateResume = async (resumeId) => {
    await runAction(resumeId, async () => {
      await api.post(`/resumes/${resumeId}/activate/`);

      setActiveResumeId(resumeId);
    });
  };

  const deleteUploadedResume = async (resumeId) => {
    const confirmed = window.confirm(
      "Delete this uploaded resume?",
    );

    if (!confirmed) return;

    await runAction(resumeId, async () => {
      await api.delete(`/resumes/${resumeId}/`);

      setUploadedResumes((current) =>
        current.filter(
          (resume) => resume.id !== resumeId,
        ),
      );

      if (activeResumeId === resumeId) {
        setActiveResumeId(null);
      }
    });
  };

  const deleteGeneratedResume = async (resumeId) => {
    const confirmed = window.confirm(
      "Delete this generated resume?",
    );

    if (!confirmed) return;

    await runAction(resumeId, async () => {
      await api.delete(
        `/resume-builder/resumes/${resumeId}/`,
      );

      setGeneratedResumes((current) =>
        current.filter(
          (resume) => resume.id !== resumeId,
        ),
      );
    });
  };

  const downloadUploadedResume = async (resume) => {
    await runAction(resume.id, async () => {
      const response = await api.get(
        `/resumes/${resume.id}/download/`,
        {
          responseType: "blob",
        },
      );

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = resume.title || "resume";

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    });
  };

  const downloadGeneratedResume = async (resume) => {
    await runAction(resume.id, async () => {
      const response = await api.get(
        `/resume-builder/resumes/${resume.id}/download/`,
        {
          responseType: "blob",
        },
      );

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `${resume.title || "resume"}.docx`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    });
  };

  const getProcessingStatus = (resume) => {
    const status = String(
      resume.processing_status || "pending",
    ).toLowerCase();

    if (status === "completed") {
      return {
        label: "AI Processing Complete",
        className: "processing-complete",
      };
    }

    if (status === "processing") {
      return {
        label: "AI Processing...",
        className: "processing-active",
      };
    }

    if (status === "failed") {
      return {
        label: "AI Processing Failed",
        className: "processing-failed",
      };
    }

    return {
      label: "Uploaded · AI Processing Pending",
      className: "processing-pending",
    };
  };

  // Initial load
  useEffect(() => {
    fetchResumes();
  }, []);

  // Poll while resume AI processing is pending/active
  useEffect(() => {
    const hasProcessingResume = uploadedResumes.some(
      (resume) =>
        resume.processing_status === "pending" ||
        resume.processing_status === "processing",
    );

    if (!hasProcessingResume) {
      return;
    }

    const interval = setInterval(() => {
      fetchResumes(false);
    }, 3000);

    return () => clearInterval(interval);
  }, [uploadedResumes]);

  if (loading) {
    return (
      <div className="page-loading">
        Loading resumes...
      </div>
    );
  }

  const hasUploaded = uploadedResumes.length > 0;
  const hasGenerated = generatedResumes.length > 0;

  const actionPending = (resumeId) =>
    actingResumeId === resumeId;

  const renderUploadedCard = (resume) => {
    const isActive = activeResumeId === resume.id;

    const processingStatus =
      getProcessingStatus(resume);

    return (
      <div
        className={`resume-card ${
          isActive ? "active" : ""
        }`}
        key={resume.id}
      >
        <div className="resume-icon">
          <FileText size={24} />
        </div>

        <div className="resume-info">
          <h3>{resume.title}</h3>

          <p>
            Uploaded{" "}
            {new Date(
              resume.uploaded_at,
            ).toLocaleDateString()}
          </p>

          <span
            className={`processing-badge ${processingStatus.className}`}
          >
            {processingStatus.className ===
              "processing-active" && (
              <Loader2
                size={14}
                className="spin"
              />
            )}

            {processingStatus.className ===
              "processing-complete" && (
              <CheckCircle2 size={14} />
            )}

            {processingStatus.className ===
              "processing-failed" && (
              <span>!</span>
            )}

            {processingStatus.label}
          </span>

          {processingStatus.className ===
            "processing-failed" &&
            resume.processing_error && (
              <p className="processing-error">
                {resume.processing_error}
              </p>
            )}
        </div>

        {isActive && (
          <div className="active-badge">
            <CheckCircle2 size={15} />
            Active
          </div>
        )}

        <div className="resume-actions">
          {!isActive && (
            <button
              onClick={() =>
                activateResume(resume.id)
              }
              disabled={actionPending(resume.id)}
            >
              {actionPending(resume.id) ? (
                <Loader2
                  size={15}
                  className="spin"
                />
              ) : (
                "Use this resume"
              )}
            </button>
          )}

          <button
            className="edit-button"
            onClick={() =>
              navigate(
                `/resumes/edit/uploaded/${resume.id}`,
              )
            }
          >
            <Pencil size={15} />
            Edit
          </button>

          <button
            className="download-button"
            onClick={() =>
              downloadUploadedResume(resume)
            }
            disabled={actionPending(resume.id)}
          >
            {actionPending(resume.id) ? (
              <Loader2
                size={15}
                className="spin"
              />
            ) : (
              <Download size={15} />
            )}
            Download
          </button>

          <button
            className="delete-button"
            onClick={() =>
              deleteUploadedResume(resume.id)
            }
            disabled={actionPending(resume.id)}
          >
            <Trash2 size={16} />
            Delete
          </button>
        </div>
      </div>
    );
  };

  const renderGeneratedCard = (resume) => {
    const status = String(
      resume.status || "draft",
    ).toLowerCase();

    return (
      <div
        className="resume-card"
        key={resume.id}
      >
        <div className="resume-icon generated">
          <Sparkles size={24} />
        </div>

        <div className="resume-info">
          <h3>{resume.title}</h3>

          <p>
            Created{" "}
            {new Date(
              resume.created_at,
            ).toLocaleDateString()}
          </p>

          <span
            className={`status-badge status-${status}`}
          >
            {status}
          </span>
        </div>

        <div className="resume-actions">
          <button
            className="edit-button"
            onClick={() =>
              navigate(
                `/resumes/edit/generated/${resume.id}`,
              )
            }
          >
            <Pencil size={15} />
            Edit
          </button>

          <button
            className="download-button"
            onClick={() =>
              downloadGeneratedResume(resume)
            }
            disabled={actionPending(resume.id)}
          >
            {actionPending(resume.id) ? (
              <Loader2
                size={15}
                className="spin"
              />
            ) : (
              <Download size={15} />
            )}
            Download
          </button>

          <button
            className="delete-button"
            onClick={() =>
              deleteGeneratedResume(resume.id)
            }
            disabled={actionPending(resume.id)}
          >
            <Trash2 size={16} />
            Delete
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="resumes-page">
      <div className="page-header">
        <div>
          <h1>My Resumes</h1>

          <p>
            Manage, edit and download your uploaded
            and generated resumes.
          </p>
        </div>
      </div>

      {error && (
        <p className="error-message">
          {error}
        </p>
      )}

      {!hasUploaded && !hasGenerated ? (
        <div className="empty-state">
          <FileText size={42} />

          <h2>No resumes yet</h2>

          <p>
            Upload your first resume from the
            dashboard or use the Resume Builder.
          </p>
        </div>
      ) : (
        <>
          <div className="resumes-tabs">
            <button
              type="button"
              className={`resume-tab ${
                activeTab === "uploaded"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                setActiveTab("uploaded")
              }
            >
              <FileText size={16} />
              Uploaded Resumes
              <span className="tab-count">
                {uploadedResumes.length}
              </span>
            </button>

            <button
              type="button"
              className={`resume-tab ${
                activeTab === "generated"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                setActiveTab("generated")
              }
            >
              <Sparkles size={16} />
              Generated Resumes
              <span className="tab-count">
                {generatedResumes.length}
              </span>
            </button>
          </div>

          {activeTab === "uploaded" &&
            (hasUploaded ? (
              <div className="resume-grid">
                {uploadedResumes.map(
                  renderUploadedCard,
                )}
              </div>
            ) : (
              <div className="empty-state">
                <h2>
                  No uploaded resumes
                </h2>

                <p>
                  Upload a PDF or DOCX resume from
                  the dashboard.
                </p>
              </div>
            ))}

          {activeTab === "generated" &&
            (hasGenerated ? (
              <div className="resume-grid">
                {generatedResumes.map(
                  renderGeneratedCard,
                )}
              </div>
            ) : (
              <div className="empty-state">
                <h2>
                  No generated resumes yet
                </h2>

                <p>
                  Use the Resume Builder to create an
                  AI-tailored resume.
                </p>
              </div>
            ))}
        </>
      )}
    </div>
  );
}

export default Resumes;