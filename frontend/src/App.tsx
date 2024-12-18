import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';
import Home from './pages/Home';
import Overview from './pages/Overview';
import Changelog from './pages/Changelog';
import Feed from './pages/Feed';

function Navigation() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav>
      <Link to="/">Home</Link>
      {isAuthenticated ? (
        <>
          <Link to="/feed">Feed</Link>
          <Link to="/overview">Overview</Link>
          <Link to="/changelog">Changelog</Link>
          <button onClick={logout}>Logout</button>
        </>
      ) : null}
    </nav>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/feed" element={<ProtectedRoute><Feed /></ProtectedRoute>} />
          <Route path="/overview" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/changelog" element={<Changelog />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;