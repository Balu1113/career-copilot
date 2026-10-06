import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import OnboardingTour from "./components/OnboardingTour";
import ProtectedRoute from "./components/ProtectedRoute";
import TopBarActions from "./components/TopBarActions";

const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Resumes = lazy(() => import("./pages/Resumes"));
const ResumeBuilder = lazy(() => import("./pages/ResumeBuilder"));
const ResumeEdit = lazy(() => import("./pages/ResumeEdit"));
const ResumeChat = lazy(() => import("./pages/ResumeChat"));
const ResumeIntelligence = lazy(() => import("./pages/ResumeIntelligence"));

const Jobs = lazy(() => import("./pages/Jobs"));
const RecommendedJobs = lazy(() => import("./pages/RecommendedJobs"));
const Applications = lazy(() => import("./pages/Applications"));

const CareerAnalysis = lazy(() => import("./pages/CareerAnalysis"));
const CareerHistory = lazy(() => import("./pages/CareerHistory"));
const CareerHistoryDetail = lazy(() => import("./pages/CareerHistoryDetail"));
const CareerRoadmap = lazy(() => import("./pages/CareerRoadmap"));

const InterviewPrep = lazy(() => import("./pages/InterviewPrep"));
const InterviewSimulator = lazy(() => import("./pages/InterviewSimulator"));
const InterviewPerformance = lazy(() => import("./pages/InterviewPerformance"));
const InterviewHistory = lazy(() => import("./pages/InterviewHistory"));
const InterviewPractice = lazy(() => import("./pages/InterviewPractice"));

const Settings = lazy(() => import("./pages/Settings"));

/* Pages that historically rendered their own <main> keep it as their
   root element. These five relied on the router providing the main
   content area, so it is applied here. */
function inMain(element) {
  return <main className="dashboard-main">{element}</main>;
}

function App() {
  return (
    <BrowserRouter>
      <OnboardingTour />
      <TopBarActions />

      <Suspense
        fallback={
          <div className="route-loading" role="status">
            Loading...
          </div>
        }
      >
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route
            path="/reset-password/:uidb64/:token"
            element={<ResetPassword />}
          />

          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />

            <Route path="/resumes" element={inMain(<Resumes />)} />
            <Route
              path="/resume-builder"
              element={inMain(<ResumeBuilder />)}
            />
            <Route
              path="/resumes/edit/:type/:id"
              element={inMain(<ResumeEdit />)}
            />
            <Route path="/resume-chat" element={<ResumeChat />} />
            <Route
              path="/resume-intelligence"
              element={<ResumeIntelligence />}
            />

            <Route path="/jobs" element={inMain(<Jobs />)} />
            <Route path="/recommended-jobs" element={<RecommendedJobs />} />
            <Route path="/applications" element={<Applications />} />

            <Route path="/career-analysis" element={<CareerAnalysis />} />
            <Route path="/career-history" element={<CareerHistory />} />
            <Route path="/career-history/:id" element={<CareerHistoryDetail />} />
            <Route path="/career-roadmap" element={<CareerRoadmap />} />

            <Route path="/interview-prep" element={<InterviewPrep />} />
            <Route
              path="/interview-simulator"
              element={<InterviewSimulator />}
            />
            <Route
              path="/interview-performance"
              element={<InterviewPerformance />}
            />
            <Route path="/interview-history" element={<InterviewHistory />} />
            <Route
              path="/interview-practice"
              element={inMain(<InterviewPractice />)}
            />

            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
