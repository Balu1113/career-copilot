import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";

import api from "../services/api";
import {
  ONBOARDING_COMPLETED_KEY,
  ONBOARDING_OPEN_EVENT,
} from "../components/OnboardingTour";
import "./Login.css";


function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setError("Email is required.");
      return;
    }

    if (!password) {
      setError("Password is required.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await api.post(
        "/auth/login/",
        {
          email: trimmedEmail,
          password,
        }
      );

      localStorage.setItem(
        "access_token",
        response.data.access
      );

      localStorage.setItem(
        "refresh_token",
        response.data.refresh
      );

      navigate("/dashboard");

      if (localStorage.getItem(ONBOARDING_COMPLETED_KEY) !== "1") {
        window.dispatchEvent(new Event(ONBOARDING_OPEN_EVENT));
      }

    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.email?.[0] ||
        "Login failed.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>AI Career Copilot</h1>
          <h2>Login</h2>
        </div>

        {location.state?.message && (
          <p className="login-notice" role="status">
            {location.state.message}
          </p>
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="password-input-shell">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                placeholder="Enter your password"
                autoComplete="current-password"
              />
              <button
                type="button"
                className="toggle-password-button"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {error && <p className="error-message">{error}</p>}

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>

          <p style={{ textAlign: "center", marginTop: "18px", fontSize: "14px", color: "var(--text-muted)" }}>
            Don&apos;t have an account? <Link to="/register" style={{ color: "var(--accent-text)", fontWeight: 500 }}>Register</Link>
          </p>

          <p style={{ textAlign: "center", marginTop: "8px", fontSize: "14px", color: "var(--text-muted)" }}>
            <Link to="/forgot-password" style={{ color: "var(--accent-text)", fontWeight: 500 }}>Forgot password?</Link>
          </p>
        </form>
      </div>
    </div>
  );
}


export default Login;
