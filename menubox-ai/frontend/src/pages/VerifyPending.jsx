import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI, clearTokens } from '../services/api';

function VerifyPending() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Get email from localStorage (set during registration)
    const pendingEmail = localStorage.getItem('pendingVerificationEmail');
    if (pendingEmail) {
      setEmail(pendingEmail);
    }

    // Check verification status every 5 seconds
    const interval = setInterval(checkVerificationStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkVerificationStatus = async () => {
    const pendingEmail = localStorage.getItem('pendingVerificationEmail');
    const pendingPassword = localStorage.getItem('pendingVerificationPassword');
    
    if (!pendingEmail || !pendingPassword) return;

    setCheckingStatus(true);
    try {
      // Try to login - if it works, email is verified
      await authAPI.login({ email: pendingEmail, password: pendingPassword });
      
      // Success! Clear pending data and go to dashboard
      localStorage.removeItem('pendingVerificationEmail');
      localStorage.removeItem('pendingVerificationPassword');
      navigate('/dashboard');
    } catch (err) {
      // Still not verified, that's okay
      setCheckingStatus(false);
    }
  };

  const handleResend = async () => {
    if (!email) return;

    setResendLoading(true);
    setError('');
    setResendSuccess(false);

    try {
      await authAPI.resendVerification(email);
      setResendSuccess(true);
    } catch (err) {
      setError('Failed to resend verification email');
    } finally {
      setResendLoading(false);
    }
  };

  const handleBackToLogin = () => {
    // Clear any stored data
    localStorage.removeItem('pendingVerificationEmail');
    localStorage.removeItem('pendingVerificationPassword');
    clearTokens();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
        <div className="text-6xl mb-6">📧</div>
        
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Check your email
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-2">
          We sent a verification link to:
        </p>
        
        <p className="font-medium text-gray-900 dark:text-white mb-6">
          {email || 'your email'}
        </p>

        <p className="text-sm text-gray-500 dark:text-gray-500 mb-6">
          Click the link in the email to verify your account. This page will automatically redirect once verified.
        </p>

        {checkingStatus && (
          <div className="mb-4 flex items-center justify-center gap-2 text-orange-500">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-orange-500 border-t-transparent"></div>
            <span className="text-sm">Checking verification status...</span>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {resendSuccess && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg text-sm">
            ✓ Verification email sent! Check your inbox.
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleResend}
            disabled={resendLoading}
            className="w-full py-2 px-4 border border-orange-500 text-orange-500 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition disabled:opacity-50"
          >
            {resendLoading ? 'Sending...' : 'Resend verification email'}
          </button>

          <button
            onClick={checkVerificationStatus}
            disabled={checkingStatus}
            className="w-full py-2 px-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition disabled:opacity-50"
          >
            {checkingStatus ? 'Checking...' : 'I\'ve verified my email'}
          </button>
        </div>

        <div className="mt-6 pt-6 border-t dark:border-gray-700">
          <button
            onClick={handleBackToLogin}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 text-sm"
          >
            ← Back to login
          </button>
        </div>

        <p className="mt-6 text-xs text-gray-400">
          Didn't receive the email? Check your spam folder.
        </p>
      </div>
    </div>
  );
}

export default VerifyPending;