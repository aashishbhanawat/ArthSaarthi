import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import NavBar from './components/NavBar';
import AdminRoute from './components/auth/AdminRoute';
import UserManagementPage from './pages/Admin/UserManagementPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />          
      <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />      
      <Route path="/admin" element={<ProtectedRoute><AdminRoute /></ProtectedRoute>}>
        <Route path="users" element={<UserManagementPage />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app-layout">
          <NavBar />
          <main className="main-content"><AppRoutes /></main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;