import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const { logout } = useAuth();

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome to your portfolio!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}