import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { repositoriesAPI } from '../services/api';

function Repositories() {
  const [repositories, setRepositories] = useState([]);
  const [githubRepos, setGithubRepos] = useState([]);
  const [bitbucketRepos, setBitbucketRepos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedRepo, setSelectedRepo] = useState('');
  const [deploymentServer, setDeploymentServer] = useState('');

  useEffect(() => {
    loadRepositories();
    loadGithubRepos();
    loadBitbucketRepos();
  }, []);

  const loadRepositories = async () => {
    try {
      const response = await repositoriesAPI.list();
      setRepositories(response.data.repositories);
    } catch (error) {
      console.error('Error loading repositories:', error);
    }
  };

  const loadGithubRepos = async () => {
    try {
      const response = await repositoriesAPI.listGithub();
      setGithubRepos(response.data.repositories);
    } catch (error) {
      console.error('Error loading GitHub repos:', error);
    }
  };

  const loadBitbucketRepos = async () => {
    try {
      const response = await repositoriesAPI.listBitbucket();
      setBitbucketRepos(response.data.repositories);
    } catch (error) {
      console.error('Error loading Bitbucket repos:', error);
    }
  };

  const handleMigrate = async () => {
    if (!selectedRepo) {
      setError('Please select a repository');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await repositoriesAPI.migrate({
        repo_name: selectedRepo,
        source: 'github',
        deployment_server: deploymentServer
      });
      setSuccess('Repository migrated successfully!');
      setSelectedRepo('');
      setDeploymentServer('');
      loadRepositories();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to migrate repository');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this repository record?')) {
      return;
    }

    try {
      await repositoriesAPI.delete(id);
      setSuccess('Repository deleted successfully');
      loadRepositories();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to delete repository');
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
          <h2>Add Repository from GitHub</h2>
          
          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <div>
            <label>
              <strong>Select GitHub Repository:</strong>
              <select 
                className="input" 
                value={selectedRepo} 
                onChange={(e) => setSelectedRepo(e.target.value)}
                disabled={loading}
              >
                <option value="">-- Select a repository --</option>
                {githubRepos.map(repo => (
                  <option key={repo.id} value={repo.name}>
                    {repo.full_name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <strong>Deployment Server (optional):</strong>
              <input
                type="text"
                className="input"
                placeholder="user@server.com:/path/to/deploy"
                value={deploymentServer}
                onChange={(e) => setDeploymentServer(e.target.value)}
                disabled={loading}
              />
            </label>

            <button 
              className="button" 
              onClick={handleMigrate}
              disabled={loading || !selectedRepo}
            >
              {loading ? 'Migrating...' : 'Migrate to Bitbucket'}
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Your Repositories</h2>
          {repositories.length === 0 ? (
            <p>No repositories yet. Migrate a GitHub repository to get started.</p>
          ) : (
            <ul className="repo-list">
              {repositories.map(repo => (
                <li key={repo.id} className="repo-item">
                  <div>
                    <strong>{repo.name}</strong>
                    <br />
                    <small>
                      Source: {repo.source} | Status: <span className={`status-badge status-${repo.status}`}>{repo.status}</span>
                    </small>
                    <br />
                    {repo.bitbucket_url && (
                      <small>
                        <a href={repo.bitbucket_url} target="_blank" rel="noopener noreferrer">
                          View in Bitbucket →
                        </a>
                      </small>
                    )}
                  </div>
                  <div className="button-group">
                    <Link to={`/pipelines/${repo.id}`}>
                      <button className="button button-secondary">Pipelines</button>
                    </Link>
                    <button 
                      className="button button-danger"
                      onClick={() => handleDelete(repo.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default Repositories;
