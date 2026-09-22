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

import { useNavigate } from "react-router-dom";


function Sidebar() {

  const navigate = useNavigate();


  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    window.location.href = "/login";
  };


  return (
    <aside className="sidebar">

      <div className="sidebar-logo">
        <Sparkles size={22} />

        <span>
          Career Copilot
        </span>
      </div>


      <nav className="sidebar-nav">

        <button
          className="nav-item active"
          onClick={() =>
            navigate("/dashboard")
          }
        >
          <BarChart3 size={18} />
          Dashboard
        </button>


        <button
  className="nav-item"
  onClick={() =>
    navigate("/resumes")
  }
>
  <FileText size={18} />
  My Resumes
</button>


        <button
          className="nav-item"
          onClick={() =>
            navigate("/career-analysis")
          }
        >
          <Sparkles size={18} />
          Career Analysis
        </button>

        <button
          className="nav-item"
          onClick={() =>
            navigate("/career-history")
          }
        >
          <Sparkles size={18} />
          Career History
        </button>


        <button className="nav-item">
          <BriefcaseBusiness size={18} />
          Job Analysis
        </button>


        <button
          className="nav-item"
          onClick={() =>
            navigate("/interview-prep")
          }
        >
          <MessageSquare size={18} />
          Interview Prep
        </button>


        <button
          className="nav-item"
          onClick={() =>
            navigate("/applications")
          }
        >
          <BriefcaseBusiness size={18} />
          Applications
        </button>

        <button
          className="nav-item"
          onClick={() =>
            navigate("/resume-chat")
          }
        >
          <MessageSquare size={18} />
          Resume AI Chat
        </button>

        <button
          className="nav-item"
          onClick={() =>
            navigate("/resume-intelligence")
          }
        >
          <Brain size={18} />
          Resume Intelligence
        </button>

        <button
          className="nav-item"
          onClick={() =>
            navigate("/settings")
          }
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