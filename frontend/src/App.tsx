import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import InterestRateManagementPage from './pages/Admin/InterestRateManagementPage';
import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import UserManagementPage from './pages/Admin/UserManagementPage';
import SystemMaintenancePage from './pages/Admin/SystemMaintenancePage';
import AdminFMVPage from './pages/Admin/AdminFMVPage';
import AdminAliasesPage from './pages/Admin/AdminAliasesPage';
import PortfolioPage from './pages/Portfolio/PortfolioPage';
import PortfolioDetailPage from './pages/Portfolio/PortfolioDetailPage';
import DataImportPage from './pages/Import/DataImportPage';
import ImportPreviewPage from './pages/Import/ImportPreviewPage';
import TransactionsPage from './pages/TransactionsPage';
import WatchlistsPage from './pages/WatchlistsPage';
import GoalsPage from './pages/GoalsPage';
import GoalDetailPage from './pages/GoalDetailPage';
import CapitalGainsPage from './pages/CapitalGainsPage';
import ProfilePage from './pages/ProfilePage';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import UpdateBanner from './components/UpdateBanner';

const AppLayout = () => (
  <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
    <UpdateBanner />
    <div className="grid grid-cols-[auto_1fr] flex-1 overflow-hidden">
      <NavBar />
      <main className="p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  </div>
);

function AppRoutes() {
  return (
    <Routes>
      {/* Public route for login, which will not have the sidebar */}
      <Route path="/login" element={<AuthPage />} />

      {/* Protected routes are wrapped in the AppLayout to get the sidebar */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/portfolios" element={<PortfolioPage />} />
          <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
          <Route path="/import" element={<DataImportPage />} />
          <Route path="/import/:sessionId/preview" element={<ImportPreviewPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/capital-gains" element={<CapitalGainsPage />} />
          <Route path="/watchlists" element={<WatchlistsPage />} />
          <Route path="/goals" element={<GoalsPage />} />
          <Route path="/goals/:goalId" element={<GoalDetailPage />} />
          <Route element={<AdminRoute />}>
            <Route path="/admin/users" element={<UserManagementPage />} />
            <Route path="/admin/interest-rates" element={<InterestRateManagementPage />} />
            <Route path="/admin/maintenance" element={<SystemMaintenancePage />} />
            <Route path="/admin/fmv" element={<AdminFMVPage />} />
            <Route path="/admin/aliases" element={<AdminAliasesPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;