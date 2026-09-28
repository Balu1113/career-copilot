import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
const Resumes = lazy(() => import("./pages/Resumes"));
const Applications = lazy(() => import("./pages/Applications"));
const InterviewPrep = lazy(() => import("./pages/InterviewPrep"));
const Settings = lazy(() => import("./pages/Settings"));
const ResumeChat = lazy(() => import("./pages/ResumeChat"));
const CareerAnalysis = lazy(() => import("./pages/CareerAnalysis"));
const CareerHistory = lazy(() => import("./pages/CareerHistory"));
const CareerHistoryDetail = lazy(() => import("./pages/CareerHistoryDetail"));
const ResumeIntelligence = lazy(() => import("./pages/ResumeIntelligence"));
const InterviewPractice = lazy(() => import("./pages/InterviewPractice"));
const ResumeBuilder = lazy(() => import("./pages/ResumeBuilder"));
const ResumeEdit = lazy(() => import("./pages/ResumeEdit"));
const Jobs = lazy(() => import("./pages/Jobs"));
const RecommendedJobs = lazy(() => import("./pages/RecommendedJobs"));
const CareerRoadmap = lazy(() => import("./pages/CareerRoadmap"));
const InterviewSimulator = lazy(() => import("./pages/InterviewSimulator"));
const InterviewHistory = lazy(() => import("./pages/InterviewHistory"));
const InterviewPerformance = lazy(() => import("./pages/InterviewPerformance"));
import OnboardingTour from "./components/OnboardingTour";
import TopBarActions from "./components/TopBarActions";

function App() {
  return (
    <BrowserRouter>
      <OnboardingTour />
      <TopBarActions />

      <Suspense fallback={<div className="route-loading" role="status">Loading...</div>}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route
          path="/reset-password/:uidb64/:token"
          element={<ResetPassword />}
        />

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

        <Route
          path="/interview-performance"
          element={
            <ProtectedRoute>
              <InterviewPerformance />
            </ProtectedRoute>
          }
        />
      </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
