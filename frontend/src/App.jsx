import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import Resumes from "./pages/Resumes";
import Sidebar from "./components/Sidebar";
import Applications from "./pages/Applications";
import InterviewPrep from "./pages/InterviewPrep";
import Settings from "./pages/Settings";
import ResumeChat from "./pages/ResumeChat";
import CareerAnalysis from "./pages/CareerAnalysis";
import CareerHistory from "./pages/CareerHistory";
import CareerHistoryDetail from "./pages/CareerHistoryDetail";
import ResumeIntelligence from "./pages/ResumeIntelligence";
import InterviewPractice from "./pages/InterviewPractice";
import ResumeBuilder from "./pages/ResumeBuilder";
import ResumeEdit from "./pages/ResumeEdit";
import Jobs from "./pages/Jobs";
import RecommendedJobs from "./pages/RecommendedJobs";
import CareerRoadmap from "./pages/CareerRoadmap";
import InterviewSimulator from "./pages/InterviewSimulator";
import InterviewHistory from "./pages/InterviewHistory";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        <Route path="/login" element={<Login />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/resumes"
          element={
            <ProtectedRoute>
              <div className="dashboard-layout">
                <Sidebar />

                <main className="dashboard-main">
                  <Resumes />
                </main>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/applications"
          element={
            <ProtectedRoute>
              <Applications />
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview-prep"
          element={
            <ProtectedRoute>
              <InterviewPrep />
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />

        <Route
          path="/resume-chat"
          element={
            <ProtectedRoute>
              <ResumeChat />
            </ProtectedRoute>
          }
        />

        <Route
          path="/career-analysis"
          element={
            <ProtectedRoute>
              <CareerAnalysis />
            </ProtectedRoute>
          }
        />

        <Route
          path="/career-history"
          element={
            <ProtectedRoute>
              <CareerHistory />
            </ProtectedRoute>
          }
        />

        <Route
          path="/career-history/:id"
          element={
            <ProtectedRoute>
              <CareerHistoryDetail />
            </ProtectedRoute>
          }
        />

        <Route
          path="/resume-intelligence"
          element={
            <ProtectedRoute>
              <ResumeIntelligence />
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview-practice"
          element={
            <ProtectedRoute>
              <InterviewPractice />
            </ProtectedRoute>
          }
        />

        <Route
          path="/resume-builder"
          element={
            <ProtectedRoute>
              <div className="dashboard-layout">
                <Sidebar />

                <main className="dashboard-main">
                  <ResumeBuilder />
                </main>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/resumes/edit/:type/:id"
          element={
            <ProtectedRoute>
              <div className="dashboard-layout">
                <Sidebar />

                <main className="dashboard-main">
                  <ResumeEdit />
                </main>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/jobs"
          element={
            <ProtectedRoute>
              <div className="dashboard-layout">
                <Sidebar />
                <main className="dashboard-main">
                  <Jobs />
                </main>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/recommended-jobs"
          element={
            <ProtectedRoute>
              <RecommendedJobs />
            </ProtectedRoute>
          }
        />

        <Route
          path="/career-roadmap"
          element={
            <ProtectedRoute>
              <CareerRoadmap />
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview-simulator"
          element={
            <ProtectedRoute>
              <InterviewSimulator />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview-history"
          element={
            <ProtectedRoute>
              <InterviewHistory />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
