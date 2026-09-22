import { useEffect, useState } from "react";
import {
  Lock,
  LogOut,
  Save,
  User,
} from "lucide-react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./Settings.css";

function Settings() {
  const [profile, setProfile] = useState({
    username: "",
    email: "",
  });

  const [passwords, setPasswords] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] =
    useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await api.get(
          "/auth/profile/"
        );

        setProfile({
          username: response.data.username || "",
          email: response.data.email || "",
        });
      } catch (err) {
        setError("Unable to load profile.");
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const updateProfile = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setMessage("");

      const response = await api.patch(
        "/auth/profile/",
        profile
      );

      setProfile({
        username: response.data.username,
        email: response.data.email,
      });

      setMessage(
        "Profile updated successfully."
      );
    } catch (err) {
      const data = err.response?.data;

      setError(
        data?.username?.[0] ||
          data?.email?.[0] ||
          "Unable to update profile."
      );
    } finally {
      setSaving(false);
    }
  };

  const updatePassword = async (event) => {
    event.preventDefault();

    try {
      setChangingPassword(true);
      setError("");
      setMessage("");

      await api.post(
        "/auth/change-password/",
        passwords
      );

      setPasswords({
        old_password: "",
        new_password: "",
        confirm_password: "",
      });

      setMessage(
        "Password changed successfully."
      );
    } catch (err) {
      const data = err.response?.data;

      setError(
        data?.error ||
          data?.confirm_password?.[0] ||
          "Unable to change password."
      );
    } finally {
      setChangingPassword(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    window.location.href = "/login";
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main settings-page">
        <div className="settings-header">
          <h1>Settings</h1>
          <p>
            Manage your profile and account settings.
          </p>
        </div>

        {message && (
          <div className="settings-success">
            {message}
          </div>
        )}

        {error && (
          <div className="settings-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="settings-loading">
            Loading profile...
          </div>
        ) : (
          <>
            <section className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon">
                  <User size={20} />
                </div>

                <div>
                  <h2>Profile</h2>
                  <p>
                    Update your account information.
                  </p>
                </div>
              </div>

              <form onSubmit={updateProfile}>
                <div className="settings-form-group">
                  <label>Username</label>

                  <input
                    type="text"
                    value={profile.username}
                    onChange={(event) =>
                      setProfile({
                        ...profile,
                        username:
                          event.target.value,
                      })
                    }
                    required
                  />
                </div>

                <div className="settings-form-group">
                  <label>Email</label>

                  <input
                    type="email"
                    value={profile.email}
                    onChange={(event) =>
                      setProfile({
                        ...profile,
                        email:
                          event.target.value,
                      })
                    }
                  />
                </div>

                <button
                  type="submit"
                  className="settings-save-btn"
                  disabled={saving}
                >
                  <Save size={17} />

                  {saving
                    ? "Saving..."
                    : "Save Changes"}
                </button>
              </form>
            </section>

            <section className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon">
                  <Lock size={20} />
                </div>

                <div>
                  <h2>Change Password</h2>
                  <p>
                    Keep your account secure with a strong
                    password.
                  </p>
                </div>
              </div>

              <form onSubmit={updatePassword}>
                <div className="settings-form-group">
                  <label>Current Password</label>

                  <input
                    type="password"
                    value={
                      passwords.old_password
                    }
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        old_password:
                          event.target.value,
                      })
                    }
                    required
                  />
                </div>

                <div className="settings-form-group">
                  <label>New Password</label>

                  <input
                    type="password"
                    value={
                      passwords.new_password
                    }
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        new_password:
                          event.target.value,
                      })
                    }
                    minLength={8}
                    required
                  />
                </div>

                <div className="settings-form-group">
                  <label>Confirm New Password</label>

                  <input
                    type="password"
                    value={
                      passwords.confirm_password
                    }
                    onChange={(event) =>
                      setPasswords({
                        ...passwords,
                        confirm_password:
                          event.target.value,
                      })
                    }
                    minLength={8}
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="settings-save-btn"
                  disabled={changingPassword}
                >
                  <Lock size={17} />

                  {changingPassword
                    ? "Changing..."
                    : "Change Password"}
                </button>
              </form>
            </section>

            <section className="settings-card danger-card">
              <div className="settings-card-header">
                <div className="settings-icon">
                  <LogOut size={20} />
                </div>

                <div>
                  <h2>Session</h2>
                  <p>
                    Sign out from this device.
                  </p>
                </div>
              </div>

              <button
                className="logout-settings-btn"
                onClick={logout}
              >
                <LogOut size={17} />
                Logout
              </button>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default Settings;