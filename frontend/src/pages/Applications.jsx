import { useEffect, useMemo, useState } from "react";
import {
  Briefcase,
  Calendar,
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
  notes: "",
};

function Applications() {
  const [applications, setApplications] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
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
          "Unable to load your applications."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

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

      const response = await api.post("/jobs/", {
        ...form,
        job_url: form.job_url || null,
        applied_date: form.applied_date || null,
      });

      setApplications((previous) => [
        response.data,
        ...previous,
      ]);

      setForm(initialForm);
      setShowForm(false);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to create the application."
      );
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (id, status) => {
    try {
      const response = await api.patch(`/jobs/${id}/`, {
        status,
      });

      setApplications((previous) =>
        previous.map((application) =>
          application.id === id
            ? response.data
            : application
        )
      );
    } catch (err) {
      setError("Unable to update application status.");
    }
  };

  const deleteApplication = async (id) => {
    const confirmed = window.confirm(
      "Delete this job application?"
    );

    if (!confirmed) {
      return;
    }

    try {
      await api.delete(`/jobs/${id}/`);

      setApplications((previous) =>
        previous.filter(
          (application) => application.id !== id
        )
      );
    } catch (err) {
      setError("Unable to delete the application.");
    }
  };

  const filteredApplications = useMemo(() => {
    if (filter === "all") {
      return applications;
    }

    return applications.filter(
      (application) => application.status === filter
    );
  }, [applications, filter]);

  const stats = useMemo(() => {
    return {
      total: applications.length,
      applied: applications.filter(
        (item) => item.status === "applied"
      ).length,
      interview: applications.filter(
        (item) => item.status === "interview"
      ).length,
      offers: applications.filter(
        (item) => item.status === "offer"
      ).length,
    };
  }, [applications]);

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
            onClick={() => setShowForm(true)}
          >
            <Plus size={18} />
            Add Application
          </button>
        </div>

        {error && (
          <div className="application-error">
            {error}
          </div>
        )}

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
              <Briefcase size={20} />
            </div>
            <div>
              <span>Offers</span>
              <strong>{stats.offers}</strong>
            </div>
          </div>
        </div>

        <div className="applications-toolbar">
          <div>
            <h2>Job Applications</h2>
            <p>
              {filteredApplications.length} application
              {filteredApplications.length !== 1 ? "s" : ""}
            </p>
          </div>

          <select
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value)
            }
          >
            <option value="all">All Applications</option>

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
              onClick={() => setShowForm(true)}
            >
              <Plus size={18} />
              Add Application
            </button>
          </div>
        ) : (
          <div className="applications-list">
            {filteredApplications.map((application) => (
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

                  <button
                    className="delete-application-btn"
                    onClick={() =>
                      deleteApplication(application.id)
                    }
                    title="Delete application"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>

                <div className="application-details">
                  {application.applied_date && (
                    <span>
                      <Calendar size={15} />
                      {application.applied_date}
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
                        event.target.value
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
            ))}
          </div>
        )}

        {showForm && (
          <div className="application-modal-overlay">
            <div className="application-modal">
              <div className="modal-header">
                <div>
                  <h2>Add Application</h2>
                  <p>
                    Save a job opportunity to your tracker.
                  </p>
                </div>

                <button
                  className="modal-close-btn"
                  onClick={() => setShowForm(false)}
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
                    onClick={() => setShowForm(false)}
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