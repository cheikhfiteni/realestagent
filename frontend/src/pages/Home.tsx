import '../App.css'
import { Auth } from '../components/Auth'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

function Home() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  console.log(isAuthenticated)
  return (
    <>
      <div style={{ margin: '0 8rem' }}>
        <p style={{ 
          color: '#666666', 
          marginBottom: '2rem',
          fontSize: '1.75rem',
          textAlign: 'left',
          textIndent: '2rem'
        }}>
          Housing is everything. On average, you'll spend 4,380 hours a year in your apartment which you'll live in for 365 days and invest 30% of your income for. You'll only spend 2-4 hours searching for it.
        </p>

        <p style={{ 
          color: '#666666', 
          marginBottom: '3rem',
          fontSize: '1.75rem', 
          textAlign: 'left',
          textIndent: '2rem'
        }}>
          At the same time, the difference between a great versus or good rental is immense. ApartmentFinder makes that easy. You give us the criteria, budget, range, and we run daily searches for the. On $20/month.
        </p>

        <div style={{ 
          marginBottom: '2rem',
          textAlign: 'left'
        }}>
          <a href="/changelog" style={{ 
            color: '#666666', 
            textDecoration: 'underline',
            fontSize: '1.75rem'
          }}>
            Changelog
          </a>
        </div>
      </div>
        {isAuthenticated ? (
          <button
            onClick={() => navigate('/overview')}
            style={{
              fontSize: '1.5rem',
              padding: '1rem 2rem',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#4CAF50',
              color: 'white',
              cursor: 'pointer',
              animation: 'bounce 1s infinite',
              '@keyframes bounce': {
                '0%, 100%': {
                  transform: 'translateY(0)'
                },
                '50%': {
                  transform: 'translateY(-10px)'
                }
              }
            }}
          >
            Find Your Next Home
          </button>
        ) : (
          <Auth />
        )}
    </>
  )
}

export default Home
