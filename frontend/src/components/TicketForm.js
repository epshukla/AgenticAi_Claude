import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import './TicketForm.css';

const TicketForm = ({ onSubmit, onClose }) => {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'bug',
    priority: 'medium',
    project_id: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.getProjects();
      const projectList = response.projects || [];
      setProjects(projectList);
      // Auto-select first project if available
      if (projectList.length > 0) {
        setFormData(prev => ({ ...prev, project_id: projectList[0].id }));
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    setLoading(true);
    await onSubmit({
      ...formData,
      creator_id: user?.id
    });
    setLoading(false);
  };

  return (
    <div className="ticket-form-overlay" onClick={onClose}>
      <div className="ticket-form-modal" onClick={e => e.stopPropagation()}>
        <div className="ticket-form-header">
          <h2>Create Ticket</h2>
          <button className="close-button" onClick={onClose}>x</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Enter ticket title"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the issue or feature..."
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="project_id">Project</label>
            <select
              id="project_id"
              name="project_id"
              value={formData.project_id}
              onChange={handleChange}
            >
              {projects.length === 0 ? (
                <option value="">No projects available</option>
              ) : (
                projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.title}
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Category</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
              >
                <option value="bug">Bug</option>
                <option value="feature">Feature</option>
                <option value="task">Task</option>
                <option value="improvement">Improvement</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="priority">Priority</label>
              <select
                id="priority"
                name="priority"
                value={formData.priority}
                onChange={handleChange}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="cancel-button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="submit-button" disabled={loading}>
              {loading ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TicketForm;
