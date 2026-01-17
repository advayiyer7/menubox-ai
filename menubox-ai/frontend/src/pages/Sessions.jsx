import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';

function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revoking, setRevoking] = useState(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await authAPI.getSessions();
      setSessions(response.data);
    } catch (err) {
      setError('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    setRevoking(sessionId);
    try {
      await authAPI.revokeSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
    } catch (err) {
      setError('Failed to revoke session');
    } finally {
      setRevoking(null);
    }
  };

  const handleLogoutAll = async () => {
    if (!confirm('This will log you out from all devices including this one. Continue?')) {
      return;
    }
    
    try {
      await authAPI.logoutAll();
      await authAPI.logout();
      navigate('/login');
    } catch (err) {
      setError('Failed to logout from all devices');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const parseDeviceInfo = (userAgent) => {
    if (!userAgent || userAgent === 'Unknown device') {
      return { device: 'Unknown', browser: 'Unknown' };
    }
    
    let device = 'Desktop';
    let browser = 'Unknown';
    
    // Detect device
    if (/iPhone/i.test(userAgent)) device = '📱 iPhone';
    else if (/iPad/i.test(userAgent)) device = '📱 iPad';
    else if (/Android/i.test(userAgent)) device = '📱 Android';
    else if (/Mac/i.test(userAgent)) device = '💻 Mac';
    else if (/Windows/i.test(userAgent)) device = '💻 Windows';
    else if (/Linux/i.test(userAgent)) device = '💻 Linux';
    else device = '💻 Desktop';
    
    // Detect browser
    if (/Chrome/i.test(userAgent) && !/Edge/i.test(userAgent)) browser = 'Chrome';
    else if (/Firefox/i.test(userAgent)) browser = 'Firefox';
    else if (/Safari/i.test(userAgent) && !/Chrome/i.test(userAgent)) browser = 'Safari';
    else if (/Edge/i.test(userAgent)) browser = 'Edge';
    
    return { device, browser };
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-2xl font-bold text-orange-600">
            🍽️ MenuBox AI
          </Link>
          <div className="flex items-center gap-4">
            <Link 
              to="/preferences" 
              className="text-gray-600 hover:text-orange-600 dark:text-gray-300"
            >
              ⚙️ Preferences
            </Link>
            <Link 
              to="/dashboard" 
              className="text-gray-600 hover:text-orange-600 dark:text-gray-300"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Active Sessions
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Manage your logged-in devices
            </p>
          </div>
          {sessions.length > 1 && (
            <button
              onClick={handleLogoutAll}
              className="px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
            >
              Logout all devices
            </button>
          )}
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-orange-500 border-t-transparent"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Loading sessions...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl">
            <p className="text-gray-600 dark:text-gray-400">No active sessions found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session, index) => {
              const { device, browser } = parseDeviceInfo(session.device_info);
              const isFirst = index === 0; // Most recent is likely current
              
              return (
                <div
                  key={session.id}
                  className={`bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm ${
                    isFirst ? 'ring-2 ring-orange-500' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-medium text-gray-900 dark:text-white">
                          {device}
                        </span>
                        {browser !== 'Unknown' && (
                          <span className="text-gray-500 dark:text-gray-400">
                            • {browser}
                          </span>
                        )}
                        {isFirst && (
                          <span className="px-2 py-0.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-xs rounded-full">
                            Current session
                          </span>
                        )}
                      </div>
                      <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        <p>Logged in: {formatDate(session.created_at)}</p>
                        <p>Expires: {formatDate(session.expires_at)}</p>
                      </div>
                    </div>
                    {!isFirst && (
                      <button
                        onClick={() => handleRevokeSession(session.id)}
                        disabled={revoking === session.id}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition disabled:opacity-50"
                      >
                        {revoking === session.id ? 'Revoking...' : 'Revoke'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
          <h3 className="font-medium text-blue-900 dark:text-blue-300">🔒 Security Tip</h3>
          <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
            If you see a device you don't recognize, revoke its session immediately and consider changing your password.
          </p>
        </div>

        <div className="mt-6">
          <Link
            to="/dashboard"
            className="text-orange-500 hover:text-orange-600"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </main>
    </div>
  );
}

export default Sessions;