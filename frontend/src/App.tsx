import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { useAuth } from "@/hooks/useAuth";
import { ClientsPage } from "@/pages/Clients";
import { ContractsPage } from "@/pages/Contracts";
import { DashboardPage } from "@/pages/Dashboard";
import { EmployeeDetailPage } from "@/pages/EmployeeDetail";
import { EmployeesPage } from "@/pages/Employees";
import { EngineersPage } from "@/pages/Engineers";
import { InvoicesPage } from "@/pages/Invoices";
import { LoginPage } from "@/pages/Login";
import { ProjectsPage } from "@/pages/Projects";
import { UsersPage } from "@/pages/Users";
import { WorkRecordsPage } from "@/pages/WorkRecords";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="flex h-screen items-center justify-center text-muted-foreground">読み込み中...</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/engineers" element={<Protected><EngineersPage /></Protected>} />
      <Route path="/clients" element={<Protected><ClientsPage /></Protected>} />
      <Route path="/projects" element={<Protected><ProjectsPage /></Protected>} />
      <Route path="/contracts" element={<Protected><ContractsPage /></Protected>} />
      <Route path="/work-records" element={<Protected><WorkRecordsPage /></Protected>} />
      <Route path="/invoices" element={<Protected><InvoicesPage /></Protected>} />
      <Route path="/employees" element={<Protected><EmployeesPage /></Protected>} />
      <Route path="/employees/:id" element={<Protected><EmployeeDetailPage /></Protected>} />
      <Route path="/users" element={<Protected><UsersPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
