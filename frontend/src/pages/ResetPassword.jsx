import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import api from "../services/api";
import "./Login.css";

function ResetPassword() {
  const { uidb64, token } = useParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.post(
        `/auth/password/reset/${uidb64}/${token}/`,
        {
          new_password: password,
          confirm_password: confirmPassword,
        },
      );
      navigate("/login", {
        replace: true,
        state: { message: "Password reset successfully. Please sign in." },
      });
    } catch (requestError) {
      const data = requestError.response?.data;
      setError(
        data?.detail ||
          data?.new_password?.[0] ||
          data?.confirm_password?.[0] ||
          "Unable to reset your password.",
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
          <h2>Choose a new password</h2>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="new-password">New password</label>
            <input
              id="new-password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm-password">Confirm new password</label>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </div>

          {error && <p className="error-message">{error}</p>}

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Updating password..." : "Reset password"}
          </button>

          <p style={{ textAlign: "center", fontSize: "14px", color: "var(--text-muted)" }}>
            <Link to="/login">Back to login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default ResetPassword;