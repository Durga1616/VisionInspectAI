import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const navigate = useNavigate();

  const role = localStorage.getItem("role");
  const isEngineer = role === "quality_engineer";

  const [inspections, setInspections] = useState([]);
  const [loadingInspections, setLoadingInspections] = useState(true);

  useEffect(() => {
    const loadInspections = async () => {
      try {
        const response = await api.get("/inspections/");
        setInspections(response.data);
      } catch (error) {
        console.error("Failed to load inspections:", error);
      } finally {
        setLoadingInspections(false);
      }
    };

    loadInspections();
  }, []);

  const totalInspections = inspections.length;

  const completedInspections = inspections.filter(
    (inspection) => inspection.status === "completed"
  ).length;

  const pendingInspections = inspections.filter(
    (inspection) => inspection.status === "pending"
  ).length;

  const defectInspections = inspections.filter(
    (inspection) =>
      inspection.result?.prediction === "defect" ||
      inspection.result?.status === "defect"
  ).length;

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    navigate("/login");
  };

  return (
    <div className="dashboard-layout">

      {/* ================= SIDEBAR ================= */}

      <aside className="dashboard-sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            V
          </div>

          <div>
            <div className="sidebar-brand-name">
              Vision<span>Inspect AI</span>
            </div>

            <div className="sidebar-brand-subtitle">
              QUALITY INTELLIGENCE
            </div>
          </div>

        </div>


        <nav className="sidebar-navigation">

          <div className="sidebar-section-title">
            WORKSPACE
          </div>

          <button className="sidebar-nav active">
            <span className="nav-icon">⌂</span>
            Dashboard
          </button>

          {isEngineer && (
            <button
              className="sidebar-nav"
              onClick={() => navigate("/inspection")}
            >
              <span className="nav-icon">▣</span>
              New Inspection
            </button>
          )}

          <button
  className="sidebar-nav"
  onClick={() => navigate("/history")}
>
  <span className="nav-icon">☷</span>
  Inspection History
</button>

          <button
  className="sidebar-nav"
  onClick={() => navigate("/analytics")}
>
  <span className="nav-icon">⌁</span>
  Analytics
</button>

          <button className="sidebar-nav">
            <span className="nav-icon">▤</span>
            Reports
          </button>

          <button className="sidebar-nav">
            <span className="nav-icon">⚙</span>
            Settings
          </button>

        </nav>


        {/* SIDEBAR INDUSTRIAL DECORATION */}

        <div className="industrial-decoration">

          <div className="factory-line line-one"></div>
          <div className="factory-line line-two"></div>

          <div className="factory-machine">
            <div className="machine-arm"></div>
            <div className="machine-joint"></div>
            <div className="machine-base"></div>
          </div>

        </div>


        <button
          className="sidebar-logout"
          onClick={logout}
        >
          <span>⇥</span>
          Logout
        </button>

      </aside>


      {/* ================= MAIN ================= */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <div>

            <h1>Dashboard</h1>

            <p>
              Overview of your inspection activities
            </p>

          </div>


          <div className="dashboard-user">

            <div className="user-avatar">
              {isEngineer ? "QE" : "FS"}
            </div>

            <div className="user-details">

              <strong>
                {isEngineer
                  ? "Quality Engineer"
                  : "Factory Supervisor"}
              </strong>

              <span>
                {isEngineer
                  ? "Inspection Team"
                  : "Production Team"}
              </span>

            </div>

            <span className="user-chevron">
             ⌄
            </span>

          </div>

        </header>


        {/* ================= WELCOME BANNER ================= */}

        <section className="welcome-banner">

          <div className="welcome-icon">
            〽
          </div>

          <div className="welcome-text">

            <h2>
              Good morning! 👋
            </h2>

            <p>
              Monitor and manage your manufacturing
              quality inspections.
            </p>

          </div>


          <div className="welcome-decoration">

            <div className="robot-arm">
              <div className="robot-top"></div>
              <div className="robot-middle"></div>
              <div className="robot-bottom"></div>
            </div>

          </div>

        </section>


        {/* ================= STAT CARDS ================= */}

        <section className="dashboard-stats">

          <div className="metric-card">

            <div className="metric-icon blue">
              ▤
            </div>

            <div className="metric-content">

              <span>Total Inspections</span>

              <strong>
                {totalInspections}
              </strong>

              <small className="blue-text">
                All time
              </small>

            </div>

          </div>


          <div className="metric-card">

            <div className="metric-icon green">
              ✓
            </div>

            <div className="metric-content">

              <span>Completed</span>

              <strong>
                {completedInspections}
              </strong>

              <small className="green-text">
                {totalInspections
                  ? Math.round(
                      (completedInspections /
                        totalInspections) *
                        100
                    )
                  : 0}
                % of total
              </small>

            </div>

          </div>


          <div className="metric-card">

            <div className="metric-icon orange">
              ◷
            </div>

            <div className="metric-content">

              <span>Pending</span>

              <strong>
                {pendingInspections}
              </strong>

              <small className="orange-text">
                {totalInspections
                  ? Math.round(
                      (pendingInspections /
                        totalInspections) *
                        100
                    )
                  : 0}
                % of total
              </small>

            </div>

          </div>


          <div className="metric-card">

            <div className="metric-icon red">
              !
            </div>

            <div className="metric-content">

              <span>Defects Detected</span>

              <strong>
                {defectInspections}
              </strong>

              <small className="red-text">
                {totalInspections
                  ? Math.round(
                      (defectInspections /
                        totalInspections) *
                        100
                    )
                  : 0}
                % of total
              </small>

            </div>

          </div>

        </section>


        {/* ================= LOWER CONTENT ================= */}

        <section className="dashboard-content-grid">

          {/* NEW INSPECTION */}

          <div className="new-inspection-card">

            <div className="section-card-header">

              <div className="section-card-icon">
                ▣
              </div>

              <div>

                <h3>
                  New Inspection
                </h3>

                <p>
                  Start a new AI-powered quality inspection
                </p>

              </div>

            </div>


            <button
              className="upload-dropzone"
              onClick={() => navigate("/inspection")}
            >

              <div className="upload-cloud">
                ↑
              </div>

              <strong>
                Upload product image
              </strong>

              <span>
                Drag & drop an image here, or click to browse
              </span>

              <small>
                Supported formats: JPG, PNG, WEBP
              </small>

              <small>
                Max file size: 10MB
              </small>

            </button>


            <button
              className="upload-button"
              onClick={() => navigate("/inspection")}
            >
              ↑ &nbsp; Upload Image
            </button>

          </div>


          {/* RECENT INSPECTIONS */}

          <div className="recent-inspections-card">

            <div className="recent-header">

              <div className="section-card-header">

                <div className="section-card-icon">
                  ☷
                </div>

                <div>

                  <h3>
                    Recent Inspections
                  </h3>

                  <p>
                    Latest inspection records
                  </p>

                </div>

              </div>

              <button className="view-all-button">
                View All →
              </button>

            </div>


            <div className="inspection-table">

              <div className="table-header">
                <span>IMAGE</span>
                <span>FILE NAME</span>
                <span>STATUS</span>
                <span>RESULT</span>
                <span>DATE</span>
              </div>


              {loadingInspections ? (

                <div className="table-empty">
                  Loading inspections...
                </div>

              ) : inspections.length === 0 ? (

                <div className="table-empty">

                  <div className="empty-icon">
                    ◌
                  </div>

                  <strong>
                    No inspections yet
                  </strong>

                  <span>
                    Your inspection records will appear here.
                  </span>

                </div>

              ) : (

                inspections
                  .slice(0, 5)
                  .map((inspection) => (

                    <div
                      className="table-row"
                      key={inspection._id}
                    >

                      <div className="inspection-thumbnail">
                        ▣
                      </div>

                      <div className="filename-cell">

                        <strong>
                          {inspection.filename}
                        </strong>

                        <span>
                          Inspection
                        </span>

                      </div>


                      <div>

                        <span
                          className={`status-pill ${
                            inspection.status
                          }`}
                        >
                          {inspection.status}
                        </span>

                      </div>


                      <div className="result-cell">
                        {inspection.result
                          ? "Available"
                          : "—"}
                      </div>


                      <div className="date-cell">
                        {inspection.created_at
                          ? new Date(
                              inspection.created_at
                            ).toLocaleDateString()
                          : "—"}
                      </div>

                    </div>

                  ))

              )}

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;