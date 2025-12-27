import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { pipelinesAPI, repositoriesAPI, coolifyAPI } from '../services/api';

function Pipelines() {
  const { repoId } = useParams();
  const [repository, setRepository] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [deploymentServer, setDeploymentServer] = useState('');
  
  // Coolify state
  const [coolifyDeployments, setCoolifyDeployments] = useState({});
  const [coolifyLogs, setCoolifyLogs] = useState({});
  const [showCoolifyLogs, setShowCoolifyLogs] = useState({});

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
      // Load Coolify deployments for this pipeline
      loadCoolifyDeployments(pipelineId);
    } catch (error) {
      console.error('Error loading pipeline details:', error);
    }
  };

  const handleTestWithCoolify = async (pipelineId) => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Create deployment in Coolify
      const response = await coolifyAPI.createDeployment({
        pipeline_id: pipelineId,
        auto_start: true
      });
      
      setSuccess('Test deployment created in Coolify!');
      
      // Start polling for status
      const deploymentId = response.data.deployment.id;
      pollDeploymentStatus(deploymentId, pipelineId);
      
      // Reload deployments
      loadCoolifyDeployments(pipelineId);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to create test deployment');
    } finally {
      setLoading(false);
    }
  };

  const loadCoolifyDeployments = async (pipelineId) => {
    try {
      const response = await coolifyAPI.listDeployments({ pipeline_id: pipelineId });
      setCoolifyDeployments(prev => ({
        ...prev,
        [pipelineId]: response.data.deployments
      }));
    } catch (error) {
      console.error('Error loading Coolify deployments:', error);
    }
  };

  const pollDeploymentStatus = async (deploymentId, pipelineId, attempts = 0) => {
    if (attempts > 60) return; // Stop after 10 minutes
    
    try {
      const response = await coolifyAPI.getDeployment(deploymentId);
      const status = response.data.deployment.status;
      
      // Update deployment in state
      setCoolifyDeployments(prev => ({
        ...prev,
        [pipelineId]: prev[pipelineId]?.map(d => 
          d.id === deploymentId ? response.data.deployment : d
        )
      }));
      
      // Continue polling if not in terminal state
      const terminalStates = ['running', 'failed', 'stopped'];
      if (!terminalStates.includes(status)) {
        setTimeout(() => pollDeploymentStatus(deploymentId, pipelineId, attempts + 1), 10000);
      }
    } catch (error) {
      console.error('Error polling deployment status:', error);
    }
  };

  const handleStopDeployment = async (deploymentId, pipelineId) => {
    try {
      await coolifyAPI.stopDeployment(deploymentId);
      setSuccess('Deployment stopped successfully');
      loadCoolifyDeployments(pipelineId);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to stop deployment');
    }
  };

  const handleDeleteDeployment = async (deploymentId, pipelineId) => {
    if (!window.confirm('Are you sure you want to delete this deployment?')) {
      return;
    }
    
    try {
      await coolifyAPI.deleteDeployment(deploymentId);
      setSuccess('Deployment deleted successfully');
      loadCoolifyDeployments(pipelineId);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to delete deployment');
    }
  };

  const handleViewLogs = async (deploymentId, pipelineId) => {
    try {
      const response = await coolifyAPI.getDeploymentLogs(deploymentId);
      setCoolifyLogs(prev => ({
        ...prev,
        [deploymentId]: response.data.logs
      }));
      setShowCoolifyLogs(prev => ({
        ...prev,
        [deploymentId]: true
      }));
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to load logs');
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
                    {(pipeline.status === 'draft' || pipeline.status === 'success') && (
                      <button 
                        className="button button-info"
                        onClick={() => handleTestWithCoolify(pipeline.id)}
                        disabled={loading}
                        title="Create test deployment in Coolify"
                      >
                        🚀 Test with Coolify
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

            {/* Coolify Deployments Section */}
            {coolifyDeployments[selectedPipeline.id] && coolifyDeployments[selectedPipeline.id].length > 0 && (
              <>
                <h4>Coolify Test Deployments</h4>
                <div className="deployments-list">
                  {coolifyDeployments[selectedPipeline.id].map(deployment => (
                    <div key={deployment.id} className="deployment-item">
                      <div className="deployment-header">
                        <strong>{deployment.application_name}</strong>
                        <span className={`status-badge status-${deployment.status}`}>
                          {deployment.status}
                        </span>
                      </div>
                      
                      <div className="deployment-details">
                        <small>Created: {new Date(deployment.created_at).toLocaleString()}</small>
                        {deployment.deployment_url && (
                          <div>
                            <a href={deployment.deployment_url} target="_blank" rel="noopener noreferrer">
                              🔗 {deployment.deployment_url}
                            </a>
                          </div>
                        )}
                      </div>

                      <div className="button-group" style={{ marginTop: '10px' }}>
                        <button 
                          className="button button-small"
                          onClick={() => handleViewLogs(deployment.id, selectedPipeline.id)}
                        >
                          View Logs
                        </button>
                        
                        {deployment.status === 'running' && (
                          <button 
                            className="button button-small button-warning"
                            onClick={() => handleStopDeployment(deployment.id, selectedPipeline.id)}
                          >
                            Stop
                          </button>
                        )}
                        
                        {deployment.status !== 'stopped' && (
                          <button 
                            className="button button-small button-danger"
                            onClick={() => handleDeleteDeployment(deployment.id, selectedPipeline.id)}
                          >
                            Delete
                          </button>
                        )}
                      </div>

                      {/* Logs display */}
                      {showCoolifyLogs[deployment.id] && coolifyLogs[deployment.id] && (
                        <div className="logs-container">
                          <div className="logs-header">
                            <h5>Deployment Logs</h5>
                            <button 
                              className="button button-small"
                              onClick={() => setShowCoolifyLogs(prev => ({ ...prev, [deployment.id]: false }))}
                            >
                              Hide Logs
                            </button>
                          </div>
                          
                          {coolifyLogs[deployment.id].build_logs && (
                            <>
                              <h6>Build Logs:</h6>
                              <div className="code-block logs-block">
                                {coolifyLogs[deployment.id].build_logs}
                              </div>
                            </>
                          )}
                          
                          {coolifyLogs[deployment.id].runtime_logs && (
                            <>
                              <h6>Runtime Logs:</h6>
                              <div className="code-block logs-block">
                                {coolifyLogs[deployment.id].runtime_logs}
                              </div>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Pipelines;
