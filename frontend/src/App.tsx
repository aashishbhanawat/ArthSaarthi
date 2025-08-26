import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import UserManagementPage from './pages/Admin/UserManagementPage';
import PortfolioPage from './pages/Portfolio/PortfolioPage';
import PortfolioDetailPage from './pages/Portfolio/PortfolioDetailPage';
import DataImportPage from './pages/Import/DataImportPage';
import ImportPreviewPage from './pages/Import/ImportPreviewPage';
import TransactionsPage from './pages/TransactionsPage';
import WatchlistsPage from './pages/WatchlistsPage';
import ErrorBoundary from './components/ErrorBoundary';

const AppLayout = () => (
  <div className="grid grid-cols-[auto_1fr] min-h-screen bg-gray-50">
    <NavBar />
    <main className="p-8 overflow-y-auto">
      <Outlet />
    </main>
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
          <Route path="/portfolios" element={<PortfolioPage />} />
          <Route path="/portfolios/:id" element={<PortfolioDetailPage />} />
          <Route path="/import" element={<DataImportPage />} />
          <Route path="/import/:sessionId/preview" element={<ImportPreviewPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/watchlists" element={<WatchlistsPage />} />
          <Route element={<AdminRoute />}>
            <Route path="/admin/users" element={<UserManagementPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AppRoutes />
    </ErrorBoundary>
  );
}

export default App;