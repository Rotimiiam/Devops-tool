import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI, repositoriesAPI } from '../services/api';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [repositories, setRepositories] = useState([]);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    checkAuthStatus();
    
    // Check for OAuth callback messages
    const authStatus = searchParams.get('auth');
    if (authStatus === 'success') {
      window.history.replaceState({}, document.title, '/dashboard');
      checkAuthStatus();
    }
  }, [searchParams]);

  const checkAuthStatus = async () => {
    try {
      const response = await authAPI.getStatus();
      if (response.data.authenticated) {
        setUser(response.data.user);
        loadRepositories();
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRepositories = async () => {
    try {
      const response = await repositoriesAPI.list();
      setRepositories(response.data.repositories);
    } catch (error) {
      console.error('Error loading repositories:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
      setUser(null);
      navigate('/');
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <div className="navbar">
        <h1>DevOps Tool</h1>
        {user && (
          <nav>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/repositories">Repositories</Link>
            <Link to="/domains">Domains</Link>
            <Link to="/settings">Settings</Link>
            <button onClick={handleLogout} className="button button-secondary" style={{ marginLeft: '1rem' }}>
              Logout
            </button>
          </nav>
        )}
      </div>

      <div className="container">
        {!user ? (
          <div className="card">
            <h2>Welcome! Please connect your accounts to get started.</h2>
            <div className="button-group">
              <button onClick={authAPI.loginBitbucket} className="button">
                Connect Bitbucket
              </button>
              <button onClick={authAPI.loginGithub} className="button">
                Connect GitHub
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="card">
              <h2>Welcome, {user.email}!</h2>
              
              <h3>Connection Status</h3>
              <div className="connection-status">
                <div className={`connection-badge ${user.bitbucket_connected ? 'connected' : 'disconnected'}`}>
                  Bitbucket: {user.bitbucket_connected ? `✓ ${user.bitbucket_username}` : '✗ Not connected'}
                </div>
                <div className={`connection-badge ${user.github_connected ? 'connected' : 'disconnected'}`}>
                  GitHub: {user.github_connected ? `✓ ${user.github_username}` : '✗ Not connected'}
                </div>
                <div className={`connection-badge ${user.gemini_configured ? 'connected' : 'disconnected'}`}>
                  Gemini API: {user.gemini_configured ? '✓ Configured' : '✗ Not configured'}
                </div>
              </div>

              {(!user.bitbucket_connected || !user.github_connected || !user.gemini_configured) && (
                <div style={{ marginTop: '1rem' }}>
                  <h4>Complete your setup:</h4>
                  <div className="button-group">
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
                    {!user.gemini_configured && (
                      <button onClick={() => navigate('/settings')} className="button">
                        Configure Gemini API
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="card">
              <h2>Your Repositories</h2>
              {repositories.length === 0 ? (
                <p>No repositories yet. <Link to="/repositories">Add a repository</Link> to get started.</p>
              ) : (
                <ul className="repo-list">
                  {repositories.slice(0, 5).map(repo => (
                    <li key={repo.id} className="repo-item">
                      <div>
                        <strong>{repo.name}</strong>
                        <br />
                        <small>Source: {repo.source} | Status: <span className={`status-badge status-${repo.status}`}>{repo.status}</span></small>
                      </div>
                      <button 
                        onClick={() => navigate(`/pipelines/${repo.id}`)} 
                        className="button button-secondary"
                      >
                        View Pipelines
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {repositories.length > 5 && (
                <Link to="/repositories">
                  <button className="button" style={{ marginTop: '1rem' }}>
                    View All Repositories
                  </button>
                </Link>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
