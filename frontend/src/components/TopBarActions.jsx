import { LogOut, User } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";

import "./TopBarActions.css";

const PUBLIC_PATHS = ["/login", "/register", "/forgot-password"];


function TopBarActions() {
  const navigate = useNavigate();
  const location = useLocation();

  const isPublic =
    PUBLIC_PATHS.includes(location.pathname) ||
    location.pathname.startsWith("/reset-password/");
  const isAuthed = Boolean(
    localStorage.getItem("access_token")
  );

  if (!isAuthed || isPublic) {
    return null;
  }

  const logout = async () => {
    const refresh = localStorage.getItem("refresh_token");
    try {
      if (refresh) await api.post("/auth/logout/", { refresh });
    } catch (error) {
      console.warn("Server-side logout failed:", error);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
  };

  return (
    <div className="topbar-actions">
      <button
        className={`topbar-action ${
          location.pathname === "/settings" ? "active" : ""
        }`}
        onClick={() => navigate("/settings")}
      >
        <User size={16} />
        My Profile
      </button>

      <button
        className="topbar-action topbar-logout"
        onClick={logout}
      >
        <LogOut size={16} />
        Logout
      </button>
    </div>
  );
}


export default TopBarActions;
