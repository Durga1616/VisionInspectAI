import { useEffect, useState } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

function Settings() {
  const [user, setUser] = useState(null);
  const [editing, setEditing] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [notifications, setNotifications] = useState(localStorage.getItem("notifications") !== "off");
  const [passwords, setPasswords] = useState({ current: "", next: "", confirm: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/auth/me")
      .then((response) => setUser(response.data.user))
      .catch((requestError) => setError(requestError.response?.data?.detail || "Unable to load your profile."));
  }, []);

  const updatePreference = (key, value) => {
    if (key === "theme") {
      setTheme(value);
      localStorage.setItem("theme", value);
    } else {
      setNotifications(value);
      localStorage.setItem("notifications", value ? "on" : "off");
    }
  };

  const savePassword = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");
    if (passwords.next !== passwords.confirm) {
      setError("New password and confirmation do not match.");
      return;
    }
    try {
      await api.post("/auth/change-password", null, {
        params: { current_password: passwords.current, new_password: passwords.next },
      });
      setMessage("Password updated successfully.");
      setPasswords({ current: "", next: "", confirm: "" });
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to update password.");
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main settings-page">
        <header className="dashboard-header">
          <div><div className="dashboard-breadcrumb">Workspace / Settings</div><h1>Settings</h1><p>Manage your profile, account security and application preferences.</p></div>
        </header>
        {message && <div className="settings-message">{message}</div>}
        {error && <div className="camera-error">{error}</div>}
        <div className="settings-grid">
          <section className="settings-card settings-profile-card">
            <div className="settings-card-heading"><div><span className="settings-eyebrow">PROFILE</span><h2>Your profile</h2></div><button type="button" onClick={() => setEditing((value) => !value)}>{editing ? "Done" : "Edit Profile"}</button></div>
            <div className="settings-profile">
              <div className="settings-avatar">{user?.name?.charAt(0)?.toUpperCase() || "U"}</div>
              <div className="settings-profile-fields">
                <label>Name<input value={user?.name || ""} readOnly={!editing} onChange={(event) => setUser({ ...user, name: event.target.value })} /></label>
                <label>Email<input value={user?.email || ""} readOnly /></label>
                <label>Role<input value={user?.role ? user.role.replace("_", " ") : ""} readOnly /></label>
              </div>
            </div>
          </section>

          <section className="settings-card">
            <div className="settings-card-heading"><div><span className="settings-eyebrow">ACCOUNT</span><h2>Change password</h2></div></div>
            <form className="settings-form" onSubmit={savePassword}>
              <label>Current Password<input type="password" required value={passwords.current} onChange={(event) => setPasswords({ ...passwords, current: event.target.value })} /></label>
              <label>New Password<input type="password" required minLength="8" value={passwords.next} onChange={(event) => setPasswords({ ...passwords, next: event.target.value })} /></label>
              <label>Confirm New Password<input type="password" required value={passwords.confirm} onChange={(event) => setPasswords({ ...passwords, confirm: event.target.value })} /></label>
              <button type="submit">Save Password</button>
            </form>
          </section>

          <section className="settings-card">
            <div className="settings-card-heading"><div><span className="settings-eyebrow">APPLICATION PREFERENCES</span><h2>Preferences</h2></div></div>
            <div className="settings-preference"><div><strong>Theme preference</strong><span>Choose the application appearance.</span></div><select value={theme} onChange={(event) => updatePreference("theme", event.target.value)}><option value="light">Light</option><option value="dark">Dark</option></select></div>
            <div className="settings-preference"><div><strong>Notifications</strong><span>Receive inspection and system notifications.</span></div><button type="button" className={`settings-toggle ${notifications ? "on" : ""}`} onClick={() => updatePreference("notifications", !notifications)} aria-pressed={notifications}><span /></button></div>
          </section>

          <section className="settings-card">
            <div className="settings-card-heading"><div><span className="settings-eyebrow">SYSTEM INFORMATION</span><h2>Platform details</h2></div></div>
            <div className="settings-system-list"><div><span>Application name</span><strong>VisionInspect AI</strong></div><div><span>Backend</span><strong>FastAPI</strong></div><div><span>Database</span><strong>PostgreSQL</strong></div><div><span>Version</span><strong>1.0.0</strong></div></div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Settings;
