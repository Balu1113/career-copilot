import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import api from "../services/api";
import "./Login.css";


function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await api.post(
        "/auth/password/reset/",
        {
          email,
        }
      );

      setSuccess(
        "If an account with that email exists, a password reset link has been sent."
      );

      setEmail("");

    } catch (error) {
      setError(
        error.response?.data?.detail ||
        error.response?.data?.email?.[0] ||
        "Failed to send reset email."
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
          <h2>Reset Password</h2>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <p style={{ marginBottom: "20px", color: "#64748b", fontSize: "14px", textAlign: "center" }}>
            Enter your email address and we&apos;ll send you a link to reset your password.
          </p>

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

          {error && <p className="error-message">{error}</p>}
          {success && <p style={{ margin: 0, fontSize: "13px", color: "#15803d", textAlign: "center" }}>{success}</p>}

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send Reset Link"}
          </button>

          <p style={{ textAlign: "center", marginTop: "18px", fontSize: "14px", color: "#64748b" }}>
            <Link to="/login" style={{ color: "#4f46e5", fontWeight: 500 }}>Back to Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}


export default ForgotPassword;