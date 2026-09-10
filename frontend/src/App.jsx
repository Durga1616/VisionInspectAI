import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Inspection from "./pages/Inspection";
import Analytics from "./pages/Analytics";
import InspectionHistory from "./pages/InspectionHistory";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/analytics" element={<Analytics />} />
        <Route
  path="/history"
  element={
    <ProtectedRoute>
      <InspectionHistory />
    </ProtectedRoute>
  }
/>
        <Route
          path="/inspection"
          element={
            <ProtectedRoute
              allowedRoles={["quality_engineer"]}
            >
              <Inspection />
            </ProtectedRoute>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;