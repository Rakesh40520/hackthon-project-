import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import Layout from "@/components/Layout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import ProjectsListPage from "@/pages/ProjectsListPage";
import ProjectDetailPage from "@/pages/ProjectDetailPage";
import VendorsPage from "@/pages/VendorsPage";
import RequirementsPage from "@/pages/RequirementsPage";
import ProposalsListPage from "@/pages/ProposalsListPage";
import ProposalDetailPage from "@/pages/ProposalDetailPage";
import ComparisonPage from "@/pages/ComparisonPage";
import AnalysisPage from "@/pages/AnalysisPage";
import RecommendationPage from "@/pages/RecommendationPage";
import ReportsPage from "@/pages/ReportsPage";
import SettingsPage from "@/pages/SettingsPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500 text-sm">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
        <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />

        <Route element={<Protected><Layout /></Protected>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsListPage />} />
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
          <Route path="/vendors" element={<VendorsPage />} />
          <Route path="/requirements" element={<RequirementsPage />} />
          <Route path="/proposals" element={<ProposalsListPage />} />
          <Route path="/proposals/:id" element={<ProposalDetailPage />} />
          <Route path="/comparison/:projectId" element={<ComparisonPage />} />
          <Route path="/analysis/:projectId" element={<AnalysisPage />} />
          <Route path="/recommendation/:projectId" element={<RecommendationPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}
