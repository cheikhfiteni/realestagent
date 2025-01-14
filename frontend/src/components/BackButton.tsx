import { ArrowLeft } from '@carbon/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function BackButton() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Only show the back button if we're not at the root
  if (location.pathname === '/') return null;

  return (
    <button
      onClick={() => navigate('/')}
      className="absolute top-6 left-6 p-2 rounded-full hover:bg-gray-100 transition-colors"
      aria-label="Go back to home"
    >
      <ArrowLeft size={24} />
    </button>
  );
} 