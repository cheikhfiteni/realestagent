import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../services/config';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export function SignIn() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/overview');
    }
  }, [isAuthenticated, navigate]);

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/request-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to request code. Please try again.');
        setIsLoading(false);
        return;
      }
      
      setShowCodeInput(true);
      // alert('Check your email for verification code'); // We can use a more integrated notification
    } catch (err) {
      console.error('Error requesting code:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, code }),
      });
      
      if (response.ok) {
        login(email); // This will trigger the useEffect to redirect
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Verification failed. Please check the code and try again.');
      }
    } catch (err) {
      console.error('Error verifying code:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg">
          {!showCodeInput ? (
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Sign in to your account
              </h2>
              <form className="mt-8 space-y-6" onSubmit={handleRequestCode}>
                <input type="hidden" name="remember" defaultValue="true" />
                <div className="rounded-md shadow-sm -space-y-px">
                  <div>
                    <label htmlFor="email-address" className="sr-only">
                      Email address
                    </label>
                    <input
                      id="email-address"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      className="appearance-none rounded-md relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                      placeholder="Email address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {error && <p className="text-sm text-red-600 text-center">{error}</p>}

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-dark disabled:opacity-50"
                  >
                    {isLoading ? 'Sending...' : 'Send Verification Code'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Enter Verification Code
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                A code has been sent to {email}.
              </p>
              <form className="mt-8 space-y-6" onSubmit={handleVerifyCode}>
                <div className="rounded-md shadow-sm -space-y-px">
                  <div>
                    <label htmlFor="verification-code" className="sr-only">
                      Verification Code
                    </label>
                    <input
                      id="verification-code"
                      name="code"
                      type="text"
                      required
                      className="appearance-none rounded-md relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                      placeholder="Verification Code"
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {error && <p className="text-sm text-red-600 text-center">{error}</p>}
                
                <div className="text-sm text-center">
                  <button
                    type="button"
                    onClick={handleRequestCode} // Re-use handleRequestCode for resend
                    disabled={isLoading}
                    className="font-medium text-primary hover:text-primary-dark disabled:opacity-50"
                  >
                    Didn't receive the code? Resend
                  </button>
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-dark disabled:opacity-50"
                  >
                    {isLoading ? 'Verifying...' : 'Verify and Sign In'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default SignIn; 