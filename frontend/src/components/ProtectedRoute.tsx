import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    console.log("Not authenticated, redirecting to home");
    return <Navigate to="/welcome" replace />;
  }

  return <>{children}</>;
}