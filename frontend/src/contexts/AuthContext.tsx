import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  email: string | null;
  login: (email: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication status on mount
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/users/me', {
        credentials: 'include', // Important for sending cookies
      });
      
      if (response.ok) {
        const user = await response.json();
        setIsAuthenticated(true);
        setEmail(user.email);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  };

  const login = (userEmail: string) => {
    setIsAuthenticated(true);
    setEmail(userEmail);
  };

  const logout = async () => {
    try {
      // Send logout request to backend
      const response = await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        credentials: 'include', // Required to send/receive cookies
      });

      // Verify the Set-Cookie header was received
      const setCookie = response.headers.get('Set-Cookie');
      if (!setCookie) {
        console.warn('No Set-Cookie header received from logout endpoint. Session cookie may not be properly cleared.');
      }
      
      // Clear frontend state
      setIsAuthenticated(false);
      setEmail(null);

      // Clear any local storage/cookies if we had them
      localStorage.removeItem('user');
      sessionStorage.clear();
      
      // For extra security, we can manually expire the session cookie
      // Note: This only works for non-HttpOnly cookies
      document.cookie = 'session=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;';
      
      // Force reload to ensure clean slate
      window.location.reload();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, email, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};