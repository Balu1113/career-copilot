import { useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../services/api";


function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post(
        "/auth/login/",
        {
          username,
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
        "Login failed."
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div>
      <h1>AI Career Copilot</h1>

      <h2>Login</h2>

      <form onSubmit={handleSubmit}>

        <div>
          <label>Username</label>

          <input
            type="text"
            value={username}
            onChange={(event) =>
              setUsername(event.target.value)
            }
            required
          />
        </div>

        <div>
          <label>Password</label>

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            required
          />
        </div>

        {error && (
          <p>{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Login"}
        </button>

      </form>
    </div>
  );
}


export default Login;