import { useState } from "react";
import { LogOut, Moon, Sun, User } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";
import { getTheme, toggleTheme } from "../services/theme";

import "./TopBarActions.css";

const PUBLIC_PATHS = ["/login", "/register", "/forgot-password"];

function TopBarActions() {
  const navigate = useNavigate();
  const location = useLocation();
  const [theme, setTheme] = useState(getTheme);

  const isPublic =
    PUBLIC_PATHS.includes(location.pathname) ||
    location.pathname.startsWith("/reset-password/");
  const isAuthed = Boolean(localStorage.getItem("access_token"));

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

  const showAccount = isAuthed && !isPublic;

  return (
    <div className="topbar-actions">
      <button
        className="topbar-action topbar-theme"
        type="button"
        onClick={() => setTheme(toggleTheme())}
        aria-label={
          theme === "dark" ? "Switch to light theme" : "Switch to dark theme"
        }
        title={theme === "dark" ? "Light mode" : "Dark mode"}
      >
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </button>

      {showAccount && (
        <>
          <button
            className={`topbar-action ${
              location.pathname === "/settings" ? "active" : ""
            }`}
            type="button"
            onClick={() => navigate("/settings")}
          >
            <User size={16} />
            My Profile
          </button>

          <button
            className="topbar-action topbar-logout"
            type="button"
            onClick={logout}
          >
            <LogOut size={16} />
            Logout
          </button>
        </>
      )}
    </div>
  );
}

export default TopBarActions;
