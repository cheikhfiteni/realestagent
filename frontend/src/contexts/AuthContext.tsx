import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { API_BASE_URL } from '../services/config';

interface AuthContextType {
  isAuthenticated: boolean;
  email: string | null;
  login: (email: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize state from localStorage if available
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const stored = localStorage.getItem('authState');
    if (stored) {
      const { isAuth, timestamp } = JSON.parse(stored);
      // Check if stored auth is less than 24 hours old
      if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
        return isAuth;
      }
      // Clear expired auth
      localStorage.removeItem('authState');
    }
    return false;
  });
  const [email, setEmail] = useState<string | null>(null);

  // Update localStorage whenever auth state changes
  useEffect(() => {
    if (isAuthenticated) {
      const stored = localStorage.getItem('authState');
      if (!stored) {
        localStorage.setItem('authState', JSON.stringify({
          isAuth: true,
          timestamp: Date.now()
        }));
      }
    } else {
      localStorage.removeItem('authState');
    }
  }, [isAuthenticated]);

  useEffect(() => {
    // Still check auth on mount to ensure token is valid
    checkAuth();
  }, []);

  // True source of auth state, checks backend to see if user is authenticated
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/users/me`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const user = await response.json();
        setIsAuthenticated(true);
        setEmail(user.email);
      } else {
        // Clear auth state if backend check fails
        setIsAuthenticated(false);
        setEmail(null);
        localStorage.removeItem('authState');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setEmail(null);
      localStorage.removeItem('authState');
    }
  };

  const login = (userEmail: string) => {
    setIsAuthenticated(true);
    setEmail(userEmail);
  };

  const logout = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
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
      localStorage.removeItem('authState');
      
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