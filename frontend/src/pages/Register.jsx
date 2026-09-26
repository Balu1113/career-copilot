import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import api from "../services/api";
import "./Login.css";


const passwordValidationRules = [
  { label: "At least 8 characters", test: (value) => value.length >= 8 },
  { label: "One uppercase letter", test: (value) => /[A-Z]/.test(value) },
  { label: "One lowercase letter", test: (value) => /[a-z]/.test(value) },
  { label: "One number", test: (value) => /\d/.test(value) },
  { label: "One special character", test: (value) => /[^A-Za-z0-9]/.test(value) },
];

function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordChecks = passwordValidationRules.map((rule) => ({
    ...rule,
    valid: rule.test(password),
  }));

  const validateForm = () => {
    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();

    if (!trimmedUsername) {
      return "Username is required.";
    }

    if (trimmedUsername.length < 3) {
      return "Username must be at least 3 characters long.";
    }

    if (!trimmedEmail) {
      return "Email is required.";
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      return "Please enter a valid email address.";
    }

    if (!password) {
      return "Password is required.";
    }

    const failedPasswordRule = passwordChecks.find((rule) => !rule.valid);
    if (failedPasswordRule) {
      return `Password must include ${failedPasswordRule.label.toLowerCase()}.`;
    }

    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }

    return "";
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const validationMessage = validateForm();
    if (validationMessage) {
      setError(validationMessage);
      window.alert(validationMessage);
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await api.post(
        "/auth/register/",
        {
          username: username.trim(),
          email: email.trim(),
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

      window.alert("Registration successful! Welcome aboard.");
      navigate("/dashboard");

    } catch (error) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.username?.[0] ||
        error.response?.data?.email?.[0] ||
        error.response?.data?.password?.[0] ||
        "Registration failed.";

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
            <div className="password-input-shell">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                placeholder="Create a password"
                autoComplete="new-password"
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

          <div className="form-group">
            <label>Confirm Password</label>
            <div className="password-input-shell">
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                placeholder="Confirm your password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="toggle-password-button"
                onClick={() => setShowConfirmPassword((current) => !current)}
                aria-label={showConfirmPassword ? "Hide confirmed password" : "Show confirmed password"}
              >
                {showConfirmPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div className="password-rules">
            {passwordChecks.map((rule) => (
              <span
                key={rule.label}
                className={rule.valid ? "password-rule valid" : "password-rule"}
              >
                {rule.label}
              </span>
            ))}
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