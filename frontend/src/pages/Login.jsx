import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import api from "../services/api";
import "./Login.css";


function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    const trimmedUsername = username.trim();

    if (!trimmedUsername) {
      const message = "Username is required.";
      setError(message);
      window.alert(message);
      return;
    }

    if (!password) {
      const message = "Password is required.";
      setError(message);
      window.alert(message);
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await api.post(
        "/auth/login/",
        {
          username: trimmedUsername,
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

      window.alert("Login successful!");
      navigate("/dashboard");

    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] ||
        "Login failed.";

      setError(message);
      window.alert(message);
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

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              placeholder="Enter your username"
              autoComplete="username"
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

          <p style={{ textAlign: "center", marginTop: "18px", fontSize: "14px", color: "#64748b" }}>
            Don&apos;t have an account? <Link to="/register" style={{ color: "#4f46e5", fontWeight: 500 }}>Register</Link>
          </p>

          <p style={{ textAlign: "center", marginTop: "8px", fontSize: "14px", color: "#64748b" }}>
            <Link to="/forgot-password" style={{ color: "#4f46e5", fontWeight: 500 }}>Forgot password?</Link>
          </p>
        </form>
      </div>
    </div>
  );
}


export default Login;