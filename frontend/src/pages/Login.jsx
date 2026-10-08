import { useEffect, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

const infoPanels = {
  features: {
    eyebrow: "BUILT FOR QUALITY TEAMS",
    title: "Inspection clarity, at every step.",
    description:
      "Bring visual checks and quality insights into one focused workspace.",
    items: [
      {
        number: "01",
        title: "Automated inspection",
        description:
          "Streamline repetitive visual checks so teams can focus on quality decisions.",
      },
      {
        number: "02",
        title: "AI-assisted detection",
        description:
          "Surface potential product anomalies with computer-vision inspection.",
      },
      {
        number: "03",
        title: "Quality analytics",
        description:
          "Review inspection outcomes and track performance from a central workspace.",
      },
    ],
    note: "Designed to support consistent, informed quality workflows.",
  },
  workflow: {
    eyebrow: "A CLEARER WORKFLOW",
    title: "From product image to quality insight.",
    description:
      "A straightforward process helps your team move from inspection to action.",
    items: [
      {
        number: "01",
        title: "Start an inspection",
        description:
          "Choose the inspection workflow that fits your operation and provide an image.",
      },
      {
        number: "02",
        title: "Review AI findings",
        description:
          "Examine detected anomalies and inspection results in context.",
      },
      {
        number: "03",
        title: "Track quality",
        description:
          "Use inspection history and analytics to follow outcomes over time.",
      },
    ],
    note: "Your available tools depend on the permissions assigned to your account.",
  },
  security: {
    eyebrow: "SECURE WORKSPACE ACCESS",
    title: "Your inspection workspace stays protected.",
    description:
      "VisionInspect AI uses authenticated access to help protect workspace features and account sessions.",
    items: [
      {
        number: "01",
        title: "Account-based sign-in",
        description:
          "Sign in with the email address and password associated with your workspace account.",
      },
      {
        number: "02",
        title: "Authenticated sessions",
        description:
          "Access to inspection tools is managed through authenticated sessions.",
      },
      {
        number: "03",
        title: "Workspace permissions",
        description:
          "Available tools are determined by the role assigned to your account.",
      },
    ],
    note: "Never share your password. Contact your workspace administrator if you suspect unauthorized access.",
  },
  help: {
    eyebrow: "SIGN-IN SUPPORT",
    title: "A little help getting started.",
    description:
      "Try these steps if you cannot access your inspection workspace.",
    items: [
      {
        number: "01",
        title: "Check your credentials",
        description:
          "Make sure you are using your work email and enter your password carefully.",
      },
      {
        number: "02",
        title: "Confirm your access",
        description:
          "Ask your workspace administrator to verify that your account is active.",
      },
      {
        number: "03",
        title: "Still having trouble?",
        description:
          "Contact your workspace administrator for account or password assistance.",
      },
    ],
    note: "For security, do not share your password in a support request.",
  },
};

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [theme, setTheme] = useState(
    () => (localStorage.getItem("theme") === "dark" ? "dark" : "light")
  );
  const [activePanel, setActivePanel] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const infoDialogRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    const dialog = infoDialogRef.current;
    if (!dialog) return;

    if (activePanel && !dialog.open) {
      dialog.showModal();
    } else if (!activePanel && dialog.open) {
      dialog.close();
    }
  }, [activePanel]);

  const setPageTheme = (nextTheme) => {
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("refresh_token", response.data.refresh_token);
      localStorage.setItem("role", response.data.role);

      navigate("/dashboard");
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to sign in. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <header className="login-header">
        <Link
          className="login-header-brand"
          to="/login"
          aria-label="VisionInspect AI home"
        >
          <span className="login-header-logo">V</span>
          <span className="login-header-wordmark">
            <strong>VisionInspect AI</strong>
            <small>QUALITY INTELLIGENCE</small>
          </span>
        </Link>

        <nav
          id="login-main-navigation"
          className={`login-header-nav${menuOpen ? " is-open" : ""}`}
          aria-label="Main navigation"
        >
          <button
            className="header-feature-link"
            type="button"
            onClick={() => {
              setActivePanel("features");
              setMenuOpen(false);
            }}
          >
            Features
          </button>
          <button
            className="header-how-link"
            type="button"
            onClick={() => {
              setActivePanel("workflow");
              setMenuOpen(false);
            }}
          >
            How It Works
          </button>
          <button
            type="button"
            onClick={() => {
              setActivePanel("security");
              setMenuOpen(false);
            }}
          >
            Security
          </button>
          <button
            type="button"
            onClick={() => {
              setActivePanel("help");
              setMenuOpen(false);
            }}
          >
            Help
          </button>
        </nav>

        <div className="login-header-actions">
          <button
            className="login-menu-toggle"
            type="button"
            aria-label={
              menuOpen ? "Close navigation menu" : "Open navigation menu"
            }
            aria-expanded={menuOpen}
            aria-controls="login-main-navigation"
            onClick={() => setMenuOpen((isOpen) => !isOpen)}
          >
            <svg
              viewBox="0 0 24 24"
              width="19"
              height="19"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              aria-hidden="true"
            >
              {menuOpen ? (
                <path d="m6 6 12 12M18 6 6 18" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" />
              )}
            </svg>
          </button>
          <div className="theme-switch" role="group" aria-label="Appearance">
            <button
              type="button"
              className={theme === "light" ? "active" : ""}
              aria-pressed={theme === "light"}
              onClick={() => setPageTheme("light")}
            >
              Day
            </button>
            <button
              type="button"
              className={theme === "dark" ? "active" : ""}
              aria-pressed={theme === "dark"}
              onClick={() => setPageTheme("dark")}
            >
              Night
            </button>
          </div>
        </div>
      </header>

      {/* LEFT BRAND PANEL */}
      <section className="login-brand">
        <div className="brand-header">
          <div className="brand-logo">V</div>

          <div>
            <h2>VisionInspect AI</h2>
            <span>QUALITY INTELLIGENCE</span>
          </div>
        </div>

        <div className="brand-content" id="how-it-works">
          <div className="eyebrow">AI-POWERED MANUFACTURING</div>

          <h1>
            Smarter
            <br />
            <span>Quality Inspection.</span>
          </h1>

          <p>
            Transform visual inspection with intelligent computer vision and
            automated defect detection.
          </p>

          <div className="feature-list" id="features">
            <div className="feature">
              <div className="feature-icon">✓</div>
              <div>
                <strong>Automated Inspection</strong>
                <span>Reduce manual quality checks</span>
              </div>
            </div>

            <div className="feature">
              <div className="feature-icon">◉</div>
              <div>
                <strong>AI-Based Detection</strong>
                <span>Identify manufacturing anomalies</span>
              </div>
            </div>

            <div className="feature">
              <div className="feature-icon">▦</div>
              <div>
                <strong>Quality Analytics</strong>
                <span>Track inspection performance</span>
              </div>
            </div>
          </div>
        </div>

        <div className="brand-footer">
          VisionInspect AI · Intelligent Quality Control
        </div>
      </section>

      {/* LOGIN PANEL */}
      <section className="login-form-section">
        <div className="login-form-container">
          <div className="form-heading">
            <span className="form-label">SECURE ACCESS</span>

            <h2>Welcome back</h2>

            <p>Sign in to access your inspection workspace.</p>
          </div>

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="login-email">Email address</label>

              <div className="input-wrapper">
                <span className="input-icon">✉</span>

                <input
                  id="login-email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>

              <div className="input-wrapper">
                <span className="input-icon">◆</span>

                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      viewBox="0 0 24 24"
                      width="19"
                      height="19"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      width="19"
                      height="19"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                      <path d="M9.9 5.2A10.7 10.7 0 0 1 12 5c6.5 0 10 7 10 7a17.2 17.2 0 0 1-3.2 4.2" />
                      <path d="M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7c1.5 0 2.8-.3 4-.8" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="login-error" role="alert">
                <span>!</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="login-spinner" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <span className="login-arrow">→</span>
                </>
              )}
            </button>
          </form>

          <div className="register-prompt">
            <span>Don't have an account?</span>
            <Link to="/register">Create account</Link>
          </div>

          <div className="security-note" id="security">
            <span>🔒</span>
            Secure authentication powered by JWT
          </div>
          <p className="login-help-note" id="help">
            Need help? Contact your workspace administrator.
          </p>
        </div>
      </section>

      <dialog
        ref={infoDialogRef}
        className="login-info-dialog"
        aria-labelledby="login-info-title"
        aria-describedby="login-info-description"
        onClose={() => setActivePanel(null)}
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            infoDialogRef.current?.close();
          }
        }}
      >
        {activePanel && (
          <div className="login-info-content">
            <div className="login-info-topline">
              <span className="login-info-icon" aria-hidden="true">
                <span />
                <span />
                <span />
                <span />
              </span>
              <button
                className="login-info-close"
                type="button"
                aria-label="Close information panel"
                onClick={() => infoDialogRef.current?.close()}
              >
                <svg
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  aria-hidden="true"
                >
                  <path d="m6 6 12 12M18 6 6 18" />
                </svg>
              </button>
            </div>

            <span className="login-info-eyebrow">
              {infoPanels[activePanel].eyebrow}
            </span>
            <h2 id="login-info-title">{infoPanels[activePanel].title}</h2>
            <p
              className="login-info-description"
              id="login-info-description"
            >
              {infoPanels[activePanel].description}
            </p>

            <div className="login-info-items">
              {infoPanels[activePanel].items.map((item) => (
                <article className="login-info-item" key={item.number}>
                  <span className="login-info-number">{item.number}</span>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                  </div>
                </article>
              ))}
            </div>

            <div className="login-info-note">
              <span aria-hidden="true">i</span>
              <p>{infoPanels[activePanel].note}</p>
            </div>

            <button
              className="login-info-done"
              type="button"
              onClick={() => infoDialogRef.current?.close()}
            >
              Back to sign in
              <span aria-hidden="true">→</span>
            </button>
          </div>
        )}
      </dialog>
    </div>
  );
}

export default Login;
