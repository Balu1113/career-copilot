import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import api from "../services/api";
import "./Login.css";


function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }

    try {
      const response = await api.post(
        "/auth/register/",
        {
          username,
          email,
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

    } catch (error) {
      setError(
        error.response?.data?.detail ||
        error.response?.data?.username?.[0] ||
        error.response?.data?.email?.[0] ||
        error.response?.data?.password?.[0] ||
        "Registration failed."
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>AI Career Copilot</h1>
          <h2>Create Account</h2>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              placeholder="Choose a username"
              autoComplete="username"
            />
          </div>

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
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              placeholder="Create a password"
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
              placeholder="Confirm your password"
              autoComplete="new-password"
            />
          </div>

          {error && <p className="error-message">{error}</p>}

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>

          <p style={{ textAlign: "center", marginTop: "18px", fontSize: "14px", color: "#64748b" }}>
            Already have an account? <Link to="/login" style={{ color: "#4f46e5", fontWeight: 500 }}>Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}


export default Register;