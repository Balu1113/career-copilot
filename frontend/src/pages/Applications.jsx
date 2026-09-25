import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  AlertCircle,
  Briefcase,
  Calendar,
  CheckCircle2,
  Edit3,
  ExternalLink,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./Applications.css";

const STATUS_OPTIONS = [
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interview", label: "Interview" },
  { value: "rejected", label: "Rejected" },
  { value: "offer", label: "Offer" },
];

const initialForm = {
  company: "",
  job_title: "",
  job_url: "",
  status: "saved",
  applied_date: "",
  follow_up_date: "",
  notes: "",
};

function Applications() {
  const location = useLocation();

  const [applications, setApplications] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  const [form, setForm] = useState(initialForm);
  const [showForm, setShowForm] = useState(false);
  const [editingApplication, setEditingApplication] = useState(null);

  const [filter, setFilter] = useState("all");

  const [loading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/jobs/");
      setApplications(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load your applications.",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);

      const response = await api.get("/jobs/analytics/");
      setAnalytics(response.data);
    } catch (err) {
      console.error("Failed to load application analytics:", err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const refreshApplicationData = async () => {
    await Promise.all([
      fetchApplications(),
      fetchAnalytics(),
    ]);
  };

  useEffect(() => {
    refreshApplicationData();
  }, []);

  useEffect(() => {
    if (location.state?.fromCareerAnalysis && location.state?.analysis) {
      const analysis = location.state.analysis;

      const recommendation = analysis.career_recommendation;
      const skillGap = analysis.skill_gap_analysis;

      const notes = [
        "Career Analysis",
        "",
        recommendation?.match_summary
          ? `Match Summary: ${recommendation.match_summary}`
          : "",
        "",
        skillGap?.missing_skills?.length
          ? `Missing Skills: ${skillGap.missing_skills
              .map((item) =>
                typeof item === "object" ? item.skill : item,
              )
              .join(", ")}`
          : "",
        "",
        recommendation?.next_steps?.length
          ? `Next Steps:\n${recommendation.next_steps
              .map((item, index) => {
                const step =
                  typeof item === "object" ? item.step : item;

                return `${index + 1}. ${step}`;
              })
              .join("\n")}`
          : "",
      ]
        .filter(Boolean)
        .join("\n");

      setForm({
        company: "",
        job_title: "",
        job_url: "",
        status: "saved",
        applied_date: "",
        follow_up_date: "",
        notes,
      });

      setShowForm(true);

      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");

      const payload = {
        ...form,
        job_url: form.job_url || null,
        applied_date: form.applied_date || null,
        follow_up_date: form.follow_up_date || null,
      };

      if (editingApplication) {
        const response = await api.patch(
          `/jobs/${editingApplication.id}/`,
          payload,
        );

        setApplications((previous) =>
          previous.map((application) =>
            application.id === editingApplication.id
              ? response.data
              : application,
          ),
        );
      } else {
        const response = await api.post("/jobs/", payload);

        setApplications((previous) => [
          response.data,
          ...previous,
        ]);
      }

      setForm(initialForm);
      setEditingApplication(null);
      setShowForm(false);

      await fetchAnalytics();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save the application.",
      );
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (id, status) => {
    try {
      setError("");

      const response = await api.patch(`/jobs/${id}/`, {
        status,
      });

      setApplications((previous) =>
        previous.map((application) =>
          application.id === id
            ? response.data
            : application,
        ),
      );

      await fetchAnalytics();
    } catch (err) {
      setError("Unable to update application status.");
    }
  };

  const handleEdit = (application) => {
    setEditingApplication(application);

    setForm({
      company: application.company || "",
      job_title: application.job_title || "",
      job_url: application.job_url || "",
      status: application.status || "saved",
      applied_date: application.applied_date || "",
      follow_up_date: application.follow_up_date || "",
      notes: application.notes || "",
    });

    setShowForm(true);
  };

  const deleteApplication = async (id) => {
    const confirmed = window.confirm(
      "Delete this job application?",
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await api.delete(`/jobs/${id}/`);

      setApplications((previous) =>
        previous.filter(
          (application) => application.id !== id,
        ),
      );

      await fetchAnalytics();
    } catch (err) {
      setError("Unable to delete the application.");
    }
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingApplication(null);
    setForm(initialForm);
  };

  const filteredApplications = useMemo(() => {
    if (filter === "all") {
      return applications;
    }

    return applications.filter(
      (application) => application.status === filter,
    );
  }, [applications, filter]);

  const stats = useMemo(() => {
    return {
      total:
        analytics?.total ?? applications.length,

      applied:
        analytics?.applied ??
        applications.filter(
          (item) => item.status === "applied",
        ).length,

      interview:
        analytics?.interview ??
        applications.filter(
          (item) => item.status === "interview",
        ).length,

      offers:
        analytics?.offer ??
        applications.filter(
          (item) => item.status === "offer",
        ).length,

      rejected:
        analytics?.rejected ??
        applications.filter(
          (item) => item.status === "rejected",
        ).length,

      followUpsDue:
        analytics?.follow_ups_due ?? 0,
    };
  }, [analytics, applications]);

  const getFollowUpState = (date) => {
    if (!date) {
      return null;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const followUpDate = new Date(`${date}T00:00:00`);
    followUpDate.setHours(0, 0, 0, 0);

    const difference =
      followUpDate.getTime() - today.getTime();

    const oneDay = 24 * 60 * 60 * 1000;

    if (difference < 0) {
      return "overdue";
    }

    if (difference === 0) {
      return "today";
    }

    if (difference <= oneDay * 3) {
      return "upcoming";
    }

    return "scheduled";
  };

  const formatFollowUpDate = (date) => {
    if (!date) {
      return "";
    }

    const parsedDate = new Date(`${date}T00:00:00`);

    return parsedDate.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main applications-page">
        <div className="applications-header">
          <div>
            <h1>Applications</h1>
            <p>
              Track your job applications and career progress.
            </p>
          </div>

          <button
            className="add-application-btn"
            onClick={() => {
              setEditingApplication(null);
              setForm(initialForm);
              setShowForm(true);
            }}
          >
            <Plus size={18} />
            Add Application
          </button>
        </div>

        {error && (
          <div className="application-error">
            <AlertCircle size={17} />
            {error}
          </div>
        )}

        {/* Application Analytics */}
        <section className="application-analytics-section">
          <div className="analytics-section-header">
            <div>
              <h2>Application Analytics</h2>
              <p>
                Track your application pipeline and progress.
              </p>
            </div>
          </div>

          {analyticsLoading && !analytics ? (
            <div className="analytics-loading">
              Loading analytics...
            </div>
          ) : (
            <>
              <div className="application-stats">
                <div className="application-stat-card">
                  <div className="stat-icon">
                    <Briefcase size={20} />
                  </div>

                  <div>
                    <span>Total Applications</span>
                    <strong>{stats.total}</strong>
                  </div>
                </div>

                <div className="application-stat-card">
                  <div className="stat-icon">
                    <Calendar size={20} />
                  </div>

                  <div>
                    <span>Applied</span>
                    <strong>{stats.applied}</strong>
                  </div>
                </div>

                <div className="application-stat-card">
                  <div className="stat-icon">
                    <Briefcase size={20} />
                  </div>

                  <div>
                    <span>Interviews</span>
                    <strong>{stats.interview}</strong>
                  </div>
                </div>

                <div className="application-stat-card">
                  <div className="stat-icon">
                    <CheckCircle2 size={20} />
                  </div>

                  <div>
                    <span>Offers</span>
                    <strong>{stats.offers}</strong>
                  </div>
                </div>

                <div className="application-stat-card">
                  <div className="stat-icon">
                    <X size={20} />
                  </div>

                  <div>
                    <span>Rejected</span>
                    <strong>{stats.rejected}</strong>
                  </div>
                </div>

                <div className="application-stat-card">
                  <div className="stat-icon">
                    <AlertCircle size={20} />
                  </div>

                  <div>
                    <span>Follow-ups Due</span>
                    <strong>{stats.followUpsDue}</strong>
                  </div>
                </div>
              </div>

              {analytics && analytics.total > 0 && (
                <div className="application-conversion">
                  <div>
                    <span>Interview Rate</span>
                    <strong>
                      {analytics.interview_rate}%
                    </strong>
                  </div>

                  <div>
                    <span>Offer Rate</span>
                    <strong>
                      {analytics.offer_rate}%
                    </strong>
                  </div>

                  <div>
                    <span>Rejection Rate</span>
                    <strong>
                      {analytics.rejection_rate}%
                    </strong>
                  </div>

                  <div>
                    <span>This Week</span>
                    <strong>
                      {analytics.applications_this_week}
                    </strong>
                  </div>

                  <div>
                    <span>This Month</span>
                    <strong>
                      {analytics.applications_this_month}
                    </strong>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        <div className="applications-toolbar">
          <div>
            <h2>Job Applications</h2>

            <p>
              {filteredApplications.length} application
              {filteredApplications.length !== 1
                ? "s"
                : ""}
            </p>
          </div>

          <select
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value)
            }
          >
            <option value="all">
              All Applications
            </option>

            {STATUS_OPTIONS.map((status) => (
              <option
                key={status.value}
                value={status.value}
              >
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="applications-loading">
            Loading applications...
          </div>
        ) : filteredApplications.length === 0 ? (
          <div className="applications-empty">
            <Briefcase size={42} />

            <h3>No applications found</h3>

            <p>
              Add your first job application to start
              tracking your career journey.
            </p>

            <button
              className="add-application-btn"
              onClick={() => {
                setEditingApplication(null);
                setForm(initialForm);
                setShowForm(true);
              }}
            >
              <Plus size={18} />
              Add Application
            </button>
          </div>
        ) : (
          <div className="applications-list">
            {filteredApplications.map((application) => {
              const followUpState =
                getFollowUpState(
                  application.follow_up_date,
                );

              return (
                <div
                  className="application-card"
                  key={application.id}
                >
                  <div className="application-card-top">
                    <div className="company-icon">
                      <Briefcase size={21} />
                    </div>

                    <div className="application-title">
                      <h3>{application.job_title}</h3>
                      <p>{application.company}</p>
                    </div>

                    <div className="application-card-actions">
                      <button
                        className="edit-application-btn"
                        onClick={() =>
                          handleEdit(application)
                        }
                        title="Edit application"
                      >
                        <Edit3 size={17} />
                      </button>

                      <button
                        className="delete-application-btn"
                        onClick={() =>
                          deleteApplication(
                            application.id,
                          )
                        }
                        title="Delete application"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>

                  <div className="application-details">
                    {application.applied_date && (
                      <span>
                        <Calendar size={15} />
                        Applied:{" "}
                        {application.applied_date}
                      </span>
                    )}

                    {application.follow_up_date && (
                      <span
                        className={`follow-up-${followUpState}`}
                      >
                        <Calendar size={15} />

                        {followUpState === "overdue" &&
                          "Follow-up overdue: "}

                        {followUpState === "today" &&
                          "Follow-up today: "}

                        {followUpState === "upcoming" &&
                          "Follow-up soon: "}

                        {followUpState ===
                          "scheduled" &&
                          "Follow-up: "}

                        {formatFollowUpDate(
                          application.follow_up_date,
                        )}
                      </span>
                    )}

                    {application.job_url && (
                      <a
                        href={application.job_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ExternalLink size={15} />
                        Job Posting
                      </a>
                    )}
                  </div>

                  <div className="application-card-bottom">
                    <select
                      value={application.status}
                      onChange={(event) =>
                        updateStatus(
                          application.id,
                          event.target.value,
                        )
                      }
                      className={`status-select status-${application.status}`}
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option
                          key={status.value}
                          value={status.value}
                        >
                          {status.label}
                        </option>
                      ))}
                    </select>

                    {application.notes && (
                      <p className="application-notes">
                        {application.notes}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {showForm && (
          <div className="application-modal-overlay">
            <div className="application-modal">
              <div className="modal-header">
                <div>
                  <h2>
                    {editingApplication
                      ? "Edit Application"
                      : "Add Application"}
                  </h2>

                  <p>
                    {editingApplication
                      ? "Update your application details."
                      : "Save a job opportunity to your tracker."}
                  </p>
                </div>

                <button
                  className="modal-close-btn"
                  onClick={closeForm}
                >
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Company</label>

                    <input
                      type="text"
                      name="company"
                      value={form.company}
                      onChange={handleChange}
                      placeholder="e.g. Accenture"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Job Title</label>

                    <input
                      type="text"
                      name="job_title"
                      value={form.job_title}
                      onChange={handleChange}
                      placeholder="e.g. AI Engineer"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Job URL</label>

                  <input
                    type="url"
                    name="job_url"
                    value={form.job_url}
                    onChange={handleChange}
                    placeholder="https://..."
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Status</label>

                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option
                          key={status.value}
                          value={status.value}
                        >
                          {status.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Applied Date</label>

                    <input
                      type="date"
                      name="applied_date"
                      value={form.applied_date}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Follow-up Date</label>

                  <input
                    type="date"
                    name="follow_up_date"
                    value={form.follow_up_date}
                    onChange={handleChange}
                  />

                  <small>
                    Set a date to remind yourself to follow
                    up on this application.
                  </small>
                </div>

                <div className="form-group">
                  <label>Notes</label>

                  <textarea
                    name="notes"
                    value={form.notes}
                    onChange={handleChange}
                    placeholder="Add notes about this application..."
                    rows="4"
                  />
                </div>

                <div className="modal-actions">
                  <button
                    type="button"
                    className="cancel-btn"
                    onClick={closeForm}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="save-application-btn"
                    disabled={saving}
                  >
                    {saving
                      ? "Saving..."
                      : editingApplication
                        ? "Save Changes"
                        : "Save Application"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Applications;