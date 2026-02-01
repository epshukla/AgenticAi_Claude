const API_BASE = '/api';

const fetchWithCredentials = async (url, options = {}) => {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
  });
  return response.json();
};

const api = {
  // Authentication
  async login(username, password) {
    return fetchWithCredentials(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
  },

  async logout() {
    return fetchWithCredentials(`${API_BASE}/auth/logout`, {
      method: 'POST',
    });
  },

  async getCurrentUser() {
    return fetchWithCredentials(`${API_BASE}/auth/me`);
  },

  async getStatus() {
    const response = await fetch(`${API_BASE}/status`);
    return response.json();
  },

  async getFiles(directory = '.') {
    const response = await fetch(`${API_BASE}/files?directory=${encodeURIComponent(directory)}`);
    return response.json();
  },

  async readFile(path) {
    const response = await fetch(`${API_BASE}/file/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return response.json();
  },

  async modifyFile(path, instruction) {
    const response = await fetch(`${API_BASE}/file/modify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, instruction }),
    });
    return response.json();
  },

  async chat(message) {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    return response.json();
  },

  async clearHistory() {
    const response = await fetch(`${API_BASE}/history/clear`, {
      method: 'POST',
    });
    return response.json();
  },

  async processTask(task) {
    const response = await fetch(`${API_BASE}/task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task }),
    });
    return response.json();
  },

  // Users
  async getUsers() {
    const response = await fetch(`${API_BASE}/users`);
    return response.json();
  },

  async createUser(username, role, email) {
    const response = await fetch(`${API_BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, role, email }),
    });
    return response.json();
  },

  // Projects
  async getProjects() {
    const response = await fetch(`${API_BASE}/projects`);
    return response.json();
  },

  async createProject(title, path, description) {
    const response = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, path, description }),
    });
    return response.json();
  },

  // Tickets
  async getTickets(projectId, status) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (status) params.append('status', status);
    const response = await fetch(`${API_BASE}/tickets?${params}`);
    return response.json();
  },

  async createTicket(ticketData) {
    const response = await fetch(`${API_BASE}/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ticketData),
    });
    return response.json();
  },

  async getTicket(ticketId) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}`);
    return response.json();
  },

  async updateTicketStatus(ticketId, status) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return response.json();
  },

  async triggerAIResolution(ticketId) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/ai-resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return response.json();
  },

  async ticketAIAction(ticketId, action, message = '') {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/ai-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, message }),
    });
    return response.json();
  },

  async ticketChat(ticketId, message) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    return response.json();
  },

  // Proposed Changes
  async getProposedChanges() {
    const response = await fetch(`${API_BASE}/proposed-changes`);
    return response.json();
  },

  async getProposedChange(changeId) {
    const response = await fetch(`${API_BASE}/proposed-changes/${changeId}`);
    return response.json();
  },

  async getTicketProposedChanges(ticketId) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/proposed-changes`);
    return response.json();
  },

  async proposeChange(ticketId, filePath, instruction) {
    const response = await fetch(`${API_BASE}/tickets/${ticketId}/propose-change`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, instruction }),
    });
    return response.json();
  },

  async acceptProposedChange(changeId) {
    const response = await fetch(`${API_BASE}/proposed-changes/${changeId}/accept`, {
      method: 'POST',
    });
    return response.json();
  },

  async rejectProposedChange(changeId) {
    const response = await fetch(`${API_BASE}/proposed-changes/${changeId}/reject`, {
      method: 'POST',
    });
    return response.json();
  },

  // Changes History
  async getChanges(projectId, limit = 50) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    params.append('limit', limit);
    const response = await fetch(`${API_BASE}/changes?${params}`);
    return response.json();
  },

  // AI Context
  async getContext(projectId, type) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (type) params.append('type', type);
    const response = await fetch(`${API_BASE}/context?${params}`);
    return response.json();
  },

  async saveContext(content, type, title, projectId, tags) {
    const response = await fetch(`${API_BASE}/context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, type, title, project_id: projectId, tags }),
    });
    return response.json();
  },

  async exportContext(filepath, projectId) {
    const response = await fetch(`${API_BASE}/context/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath, project_id: projectId }),
    });
    return response.json();
  },
};

export { api };
export default api;
