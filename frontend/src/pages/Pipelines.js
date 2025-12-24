import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { pipelinesAPI, repositoriesAPI } from '../services/api';

function Pipelines() {
  const { repoId } = useParams();
  const [repository, setRepository] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deploymentServer, setDeploymentServer] = useState('');

  useEffect(() => {
    loadRepository();
    loadPipelines();
  }, [repoId]);

  const loadRepository = async () => {
    try {
      const response = await repositoriesAPI.get(repoId);
      setRepository(response.data);
    } catch (error) {
      setError('Failed to load repository');
    }
  };

  const loadPipelines = async () => {
    try {
      const response = await pipelinesAPI.list(repoId);
      setPipelines(response.data.pipelines);
    } catch (error) {
      console.error('Error loading pipelines:', error);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await pipelinesAPI.generate({
        repository_id: repoId,
        deployment_server: deploymentServer
      });
      setSuccess('Pipeline generated successfully!');
      loadPipelines();
      setSelectedPipeline(response.data.pipeline);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (pipelineId) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await pipelinesAPI.test({ pipeline_id: pipelineId });
      if (response.data.result.success) {
        setSuccess('Pipeline test passed!');
      } else {
        setError(`Pipeline test failed: ${response.data.result.error}`);
      }
      loadPipelines();
      loadPipelineDetails(pipelineId);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to test pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleIterate = async (pipelineId) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await pipelinesAPI.iterate({ pipeline_id: pipelineId });
      setSuccess('New pipeline version created!');
      loadPipelines();
      setSelectedPipeline(response.data.pipeline);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to iterate pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePR = async (pipelineId) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await pipelinesAPI.createPR({ pipeline_id: pipelineId });
      setSuccess(`Pull request created! ${response.data.pr_url}`);
      loadPipelines();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to create pull request');
    } finally {
      setLoading(false);
    }
  };

  const loadPipelineDetails = async (pipelineId) => {
    try {
      const response = await pipelinesAPI.get(pipelineId);
      setSelectedPipeline(response.data);
    } catch (error) {
      console.error('Error loading pipeline details:', error);
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
        {repository && (
          <div className="card">
            <h2>Pipelines for {repository.name}</h2>
            <p>Status: <span className={`status-badge status-${repository.status}`}>{repository.status}</span></p>
            
            {error && <div className="error">{error}</div>}
            {success && <div className="success">{success}</div>}

            {pipelines.length === 0 && (
              <div>
                <p>No pipelines yet. Generate one to get started.</p>
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
                  onClick={handleGenerate}
                  disabled={loading}
                >
                  {loading ? 'Generating...' : 'Generate Pipeline'}
                </button>
              </div>
            )}
          </div>
        )}

        {pipelines.length > 0 && (
          <div className="card">
            <h3>Pipeline Versions</h3>
            <ul className="pipeline-list">
              {pipelines.map(pipeline => (
                <li key={pipeline.id} className="pipeline-item">
                  <div>
                    <strong>Version {pipeline.version}</strong>
                    <br />
                    <small>
                      Status: <span className={`status-badge status-${pipeline.status}`}>{pipeline.status}</span>
                      {pipeline.pr_created && (
                        <span> | <a href={pipeline.pr_url} target="_blank" rel="noopener noreferrer">View PR →</a></span>
                      )}
                    </small>
                  </div>
                  <div className="button-group">
                    <button 
                      className="button button-secondary"
                      onClick={() => loadPipelineDetails(pipeline.id)}
                    >
                      View Details
                    </button>
                    {pipeline.status === 'draft' && (
                      <button 
                        className="button"
                        onClick={() => handleTest(pipeline.id)}
                        disabled={loading}
                      >
                        Test
                      </button>
                    )}
                    {pipeline.status === 'failed' && (
                      <button 
                        className="button button-secondary"
                        onClick={() => handleIterate(pipeline.id)}
                        disabled={loading}
                      >
                        Fix with AI
                      </button>
                    )}
                    {pipeline.status === 'success' && !pipeline.pr_created && (
                      <button 
                        className="button button-success"
                        onClick={() => handleCreatePR(pipeline.id)}
                        disabled={loading}
                      >
                        Create PR
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {selectedPipeline && (
          <div className="card">
            <h3>Pipeline Version {selectedPipeline.version} Details</h3>
            <p>Status: <span className={`status-badge status-${selectedPipeline.status}`}>{selectedPipeline.status}</span></p>
            
            <h4>Configuration:</h4>
            <div className="code-block">{selectedPipeline.config}</div>

            {selectedPipeline.test_output && (
              <>
                <h4>Test Output:</h4>
                <div className="code-block">{selectedPipeline.test_output}</div>
              </>
            )}

            {selectedPipeline.error_message && (
              <>
                <h4>Error Message:</h4>
                <div className="error">{selectedPipeline.error_message}</div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Pipelines;
