import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { settingsAPI, authAPI } from '../services/api';

function Settings() {
  const [user, setUser] = useState(null);
  const [geminiKey, setGeminiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const authResponse = await authAPI.getStatus();
      if (authResponse.data.authenticated) {
        setUser(authResponse.data.user);
      }
      
      const response = await settingsAPI.get();
      // Settings loaded
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const handleSaveGeminiKey = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await settingsAPI.updateGeminiKey(geminiKey);
      setSuccess('Gemini API key saved successfully!');
      setGeminiKey('');
      loadSettings();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to save API key');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGeminiKey = async () => {
    if (!window.confirm('Are you sure you want to remove your Gemini API key?')) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await settingsAPI.deleteGeminiKey();
      setSuccess('Gemini API key removed successfully');
      loadSettings();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to remove API key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="navbar">
        <h1>DevOps Tool</h1>
        <nav>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/repositories">Repositories</Link>
          <Link to="/domains">Domains</Link>
          <Link to="/settings">Settings</Link>
        </nav>
      </div>

      <div className="container">
        <div className="card">
          <h2>Settings</h2>
          
          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          {user && (
            <>
              <h3>Account Connections</h3>
              <div className="connection-status" style={{ marginBottom: '2rem' }}>
                <div className={`connection-badge ${user.bitbucket_connected ? 'connected' : 'disconnected'}`}>
                  Bitbucket: {user.bitbucket_connected ? `✓ ${user.bitbucket_username}` : '✗ Not connected'}
                </div>
                <div className={`connection-badge ${user.github_connected ? 'connected' : 'disconnected'}`}>
                  GitHub: {user.github_connected ? `✓ ${user.github_username}` : '✗ Not connected'}
                </div>
              </div>

              {(!user.bitbucket_connected || !user.github_connected) && (
                <div className="button-group" style={{ marginBottom: '2rem' }}>
                  {!user.bitbucket_connected && (
                    <button onClick={authAPI.loginBitbucket} className="button">
                      Connect Bitbucket
                    </button>
                  )}
                  {!user.github_connected && (
                    <button onClick={authAPI.loginGithub} className="button">
                      Connect GitHub
                    </button>
                  )}
                </div>
              )}
            </>
          )}

          <h3>Gemini API Configuration</h3>
          {user?.gemini_configured ? (
            <div>
              <p className="success">✓ Gemini API key is configured</p>
              <button 
                className="button button-danger"
                onClick={handleDeleteGeminiKey}
                disabled={loading}
              >
                Remove API Key
              </button>
            </div>
          ) : (
            <form onSubmit={handleSaveGeminiKey}>
              <label>
                <strong>Gemini 3 Pro API Key:</strong>
                <input
                  type="password"
                  className="input"
                  placeholder="Enter your Gemini API key"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  required
                  disabled={loading}
                />
              </label>
              <button type="submit" className="button" disabled={loading}>
                {loading ? 'Saving...' : 'Save API Key'}
              </button>
            </form>
          )}

          <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
            <h4>How to get a Gemini API key:</h4>
            <ol>
              <li>Visit <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a></li>
              <li>Sign in with your Google account</li>
              <li>Create a new API key</li>
              <li>Copy the key and paste it above</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
