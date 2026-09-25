import {
  Brain,
  BarChart3,
  BriefcaseBusiness,
  FileText,
  LogOut,
  MessageSquare,
  Settings,
  Sparkles,
} from "lucide-react";

import { useNavigate, useLocation } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    window.location.href = "/login";
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Sparkles size={22} />
        <span>Career Copilot</span>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`nav-item ${
            isActive("/dashboard") ? "active" : ""
          }`}
          onClick={() => navigate("/dashboard")}
        >
          <BarChart3 size={18} />
          Dashboard
        </button>

        <button
          className={`nav-item ${
            isActive("/resumes") ? "active" : ""
          }`}
          onClick={() => navigate("/resumes")}
        >
          <FileText size={18} />
          My Resumes
        </button>

        <button
          className={`nav-item ${
            isActive("/resume-builder") ? "active" : ""
          }`}
          onClick={() => navigate("/resume-builder")}
        >
          <FileText size={18} />
          Resume Builder
        </button>

        <button
          className={`nav-item ${
            isActive("/career-analysis") ? "active" : ""
          }`}
          onClick={() => navigate("/career-analysis")}
        >
          <Sparkles size={18} />
          Career Analysis
        </button>

        <button
          className={`nav-item ${
            isActive("/career-history") ? "active" : ""
          }`}
          onClick={() => navigate("/career-history")}
        >
          <Sparkles size={18} />
          Career History
        </button>

        <button
          className={`nav-item ${
            isActive("/interview-prep") ? "active" : ""
          }`}
          onClick={() => navigate("/interview-prep")}
        >
          <MessageSquare size={18} />
          Interview Prep
        </button>

        <button
          className={`nav-item ${
            isActive("/jobs") ? "active" : ""
          }`}
          onClick={() => navigate("/jobs")}
        >
          <BriefcaseBusiness size={18} />
          Jobs
        </button>

        <button
          className={`nav-item ${
            isActive("/recommended-jobs")
              ? "active"
              : ""
          }`}
          onClick={() => navigate("/recommended-jobs")}
        >
          <Sparkles size={18} />
          Recommended Jobs
        </button>

        <button
          className={`nav-item ${
            isActive("/applications") ? "active" : ""
          }`}
          onClick={() => navigate("/applications")}
        >
          <BriefcaseBusiness size={18} />
          Applications
        </button>

        <button
          className={`nav-item ${
            isActive("/resume-chat") ? "active" : ""
          }`}
          onClick={() => navigate("/resume-chat")}
        >
          <MessageSquare size={18} />
          Resume AI Chat
        </button>

        <button
          className={`nav-item ${
            isActive("/resume-intelligence")
              ? "active"
              : ""
          }`}
          onClick={() => navigate("/resume-intelligence")}
        >
          <Brain size={18} />
          Resume Intelligence
        </button>

        <button
          className={`nav-item ${
            isActive("/settings") ? "active" : ""
          }`}
          onClick={() => navigate("/settings")}
        >
          <Settings size={18} />
          Settings
        </button>
      </nav>

      <div className="sidebar-bottom">
        <button
          className="nav-item logout"
          onClick={logout}
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;