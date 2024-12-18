// frontend/src/components/Auth.tsx
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export function Auth() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const requestCode = async () => {
    try {
      console.log('Sending request with email:', email);
      const response = await fetch('http://localhost:8000/auth/request-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        alert(`Error: ${errorData.detail || 'Something went wrong'}`);
        return;
      }
      
      setShowCodeInput(true);
      alert('Check your email for verification code');
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const verifyCode = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/verify-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, code }),
      });
      
      if (response.ok) {
        login(email);
        navigate('/feed');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail || 'Verification failed'}`);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
      />
      <button onClick={requestCode}>Request Code</button>

      {showCodeInput && (
        <>
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter verification code"
          />
          <button onClick={verifyCode}>Verify Code</button>
        </>
      )}
    </div>
  );
}