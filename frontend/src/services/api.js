import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authAPI = {
  getStatus: () => apiClient.get('/api/auth/status'),
  logout: () => apiClient.post('/api/auth/logout'),
  loginBitbucket: () => {
    window.location.href = `${API_BASE_URL}/api/auth/bitbucket/login`;
  },
  loginGithub: () => {
    window.location.href = `${API_BASE_URL}/api/auth/github/login`;
  },
};

export const repositoriesAPI = {
  listGithub: () => apiClient.get('/api/repositories/github'),
  listBitbucket: () => apiClient.get('/api/repositories/bitbucket'),
  list: () => apiClient.get('/api/repositories/'),
  get: (id) => apiClient.get(`/api/repositories/${id}`),
  migrate: (data) => apiClient.post('/api/repositories/migrate', data),
  delete: (id) => apiClient.delete(`/api/repositories/${id}`),
};

export const pipelinesAPI = {
  generate: (data) => apiClient.post('/api/pipelines/generate', data),
  test: (data) => apiClient.post('/api/pipelines/test', data),
  iterate: (data) => apiClient.post('/api/pipelines/iterate', data),
  createPR: (data) => apiClient.post('/api/pipelines/create-pr', data),
  list: (repoId) => apiClient.get(`/api/pipelines/repository/${repoId}`),
  get: (id) => apiClient.get(`/api/pipelines/${id}`),
};

export const domainsAPI = {
  list: () => apiClient.get('/api/domains/'),
  get: (id) => apiClient.get(`/api/domains/${id}`),
  create: (data) => apiClient.post('/api/domains/', data),
  update: (id, data) => apiClient.put(`/api/domains/${id}`, data),
  delete: (id) => apiClient.delete(`/api/domains/${id}`),
};

export const settingsAPI = {
  get: () => apiClient.get('/api/settings/'),
  updateGeminiKey: (apiKey) => apiClient.post('/api/settings/gemini-api-key', { api_key: apiKey }),
  deleteGeminiKey: () => apiClient.delete('/api/settings/gemini-api-key'),
};

export const coolifyAPI = {
  // Health check
  checkHealth: () => apiClient.get('/api/coolify/health'),
  
  // Deployments
  createDeployment: (data) => apiClient.post('/api/coolify/deployments', data),
  listDeployments: (params) => apiClient.get('/api/coolify/deployments', { params }),
  getDeployment: (id) => apiClient.get(`/api/coolify/deployments/${id}`),
  deleteDeployment: (id) => apiClient.delete(`/api/coolify/deployments/${id}`),
  
  // Deployment operations
  startDeployment: (id) => apiClient.post(`/api/coolify/deployments/${id}/start`),
  stopDeployment: (id) => apiClient.post(`/api/coolify/deployments/${id}/stop`),
  
  // Logs
  getDeploymentLogs: (id, logType = 'combined') => 
    apiClient.get(`/api/coolify/deployments/${id}/logs`, { params: { type: logType } }),
  
  // Cleanup
  cleanupOld: (ageHours = 24) => 
    apiClient.post('/api/coolify/cleanup/old', null, { params: { age_hours: ageHours } }),
};

export default apiClient;
