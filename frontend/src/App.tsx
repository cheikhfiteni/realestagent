import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import Home from './pages/Home';
import Overview from './pages/Overview';
import Changelog from './pages/Changelog';
import Feed from './pages/Feed';
import BackButton from './components/BackButton';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <BackButton />
        <Routes>
          <Route path="/welcome" element={<Home />} />
          <Route path="/" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/feed/:jobId" element={<ProtectedRoute><Feed /></ProtectedRoute>} />
          <Route path="/overview" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/changelog" element={<Changelog />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;