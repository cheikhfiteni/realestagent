import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import Home from './pages/Home';
import Overview from './pages/Overview';
import Changelog from './pages/Changelog';
import Feed from './pages/Feed';
import BackButton from './components/BackButton';
import { Link } from 'react-router-dom';

function Footer() {
  const { logout, isAuthenticated } = useAuth();
  const location = useLocation();
  
  // Don't render footer on welcome page
  if (location.pathname === '/welcome') return null;
  
  return (
    <footer className="w-full mt-auto py-6">
      <div className="max-w-[768px] mx-auto px-8">
        <div className="flex justify-between items-center text-sm text-gray-500">
          <div className="space-x-6">
            <Link to="/overview" className="hover:text-gray-900">Overview</Link>
            <Link to="/changelog" className="hover:text-gray-900">Changelog</Link>
            <Link to="/welcome" className="hover:text-gray-900">About</Link>
          </div>
          {isAuthenticated && (
            <button
              onClick={logout}
              className="hover:text-gray-900"
            >
              Logout
            </button>
          )}
        </div>
      </div>
    </footer>
  );
}

function AppContent() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const showFooter = isAuthenticated && location.pathname !== '/welcome';
  const showBackButton = isAuthenticated && location.pathname !== '/welcome' && location.pathname !== '/overview';

  return (
    <div className="min-h-screen flex flex-col">
      {showBackButton && <BackButton />}
      <main className="flex-grow flex flex-col w-full">
        <Routes>
          <Route path="/welcome" element={<Home />} />
          <Route path="/" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/feed/:jobId" element={<ProtectedRoute><Feed /></ProtectedRoute>} />
          <Route path="/overview" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/changelog" element={<Changelog />} />
        </Routes>
      </main>
      {showFooter && <Footer />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;