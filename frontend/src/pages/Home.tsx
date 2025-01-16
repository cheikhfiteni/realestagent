import '../App.css'
import { Auth } from '../components/Auth'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

function Home() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Disable scrolling
    document.body.style.overflow = 'hidden';
    
    // Re-enable scrolling on cleanup
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  return (
    <div className="flex-grow flex items-center justify-center animate-fadeIn">
      <div className="max-w-4xl w-full px-8">
        <div className="space-y-6">
          <p className="text-gray-600 text-xl leading-relaxed indent-8">
            Housing is everything. On average, you'll spend 4,380 hours a year in your apartment which you'll live in for 365 days and invest 30% of your income for. You'll only spend 2-4 hours searching for it.
          </p>

          <p className="text-gray-600 text-xl leading-relaxed indent-8">
            At the same time, the difference between a great versus or good rental is immense. ApartmentFinder makes that easy. You give us the criteria, budget, range, and we run daily searches for the. On $20/month.
          </p>

          <div className="text-left">
            <a href="/changelog" className="text-gray-600 text-xl underline hover:text-gray-900">
              Changelog
            </a>
          </div>
        </div>

        <div className="mt-8">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/overview')}
              className="text-xl px-8 py-4 rounded-lg bg-green-500 text-white hover:bg-green-600 transition-colors animate-shake"
            >
              Find Your Next Home
            </button>
          ) : (
            <Auth />
          )}
        </div>
      </div>
    </div>
  )
}

export default Home
