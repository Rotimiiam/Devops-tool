import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { domainsAPI } from '../services/api';

function Domains() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    is_root: false,
    parent_domain_id: '',
    description: ''
  });

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      const response = await domainsAPI.list();
      setDomains(response.data.domains);
    } catch (error) {
      console.error('Error loading domains:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await domainsAPI.create(formData);
      setSuccess('Domain created successfully!');
      setFormData({ name: '', is_root: false, parent_domain_id: '', description: '' });
      setShowForm(false);
      loadDomains();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to create domain');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this domain?')) {
      return;
    }

    try {
      await domainsAPI.delete(id);
      setSuccess('Domain deleted successfully');
      loadDomains();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to delete domain');
    }
  };

  const rootDomains = domains.filter(d => d.is_root);
  const hasRootDomain = rootDomains.length > 0;

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
          <h2>Domain Management</h2>
          
          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <button 
            className="button" 
            onClick={() => setShowForm(!showForm)}
            style={{ marginBottom: '1rem' }}
          >
            {showForm ? 'Cancel' : 'Add Domain'}
          </button>

          {showForm && (
            <form onSubmit={handleSubmit}>
              <label>
                <strong>Domain Name:</strong>
                <input
                  type="text"
                  className="input"
                  placeholder="example.com or subdomain"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  disabled={loading}
                />
              </label>

              {!hasRootDomain && (
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_root}
                    onChange={(e) => setFormData({ ...formData, is_root: e.target.checked })}
                    disabled={loading}
                  />
                  <strong> Root Domain</strong>
                </label>
              )}

              {hasRootDomain && !formData.is_root && (
                <label>
                  <strong>Parent Domain:</strong>
                  <select
                    className="input"
                    value={formData.parent_domain_id}
                    onChange={(e) => setFormData({ ...formData, parent_domain_id: e.target.value })}
                    disabled={loading}
                  >
                    <option value="">-- Select parent domain --</option>
                    {domains.map(domain => (
                      <option key={domain.id} value={domain.id}>
                        {domain.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              <label>
                <strong>Description:</strong>
                <input
                  type="text"
                  className="input"
                  placeholder="Optional description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  disabled={loading}
                />
              </label>

              <button type="submit" className="button" disabled={loading}>
                {loading ? 'Creating...' : 'Create Domain'}
              </button>
            </form>
          )}
        </div>

        <div className="card">
          <h3>Your Domains</h3>
          {domains.length === 0 ? (
            <p>No domains configured yet.</p>
          ) : (
            <ul className="domain-list">
              {domains.map(domain => (
                <li key={domain.id} className="domain-item">
                  <div>
                    <strong>{domain.name}</strong>
                    {domain.is_root && <span className="status-badge status-success" style={{ marginLeft: '0.5rem' }}>ROOT</span>}
                    <br />
                    <small>{domain.description || 'No description'}</small>
                    {domain.parent_domain_id && (
                      <>
                        <br />
                        <small>Parent: {domains.find(d => d.id === domain.parent_domain_id)?.name}</small>
                      </>
                    )}
                  </div>
                  <button 
                    className="button button-danger"
                    onClick={() => handleDelete(domain.id)}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default Domains;
