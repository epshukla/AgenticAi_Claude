import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import api from '../services/api';
import './TicketDetailPage.css';

const TicketDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Proposed changes state
  const [proposedChanges, setProposedChanges] = useState([]);
  const [showProposeForm, setShowProposeForm] = useState(false);
  const [proposeFilePath, setProposeFilePath] = useState('');
  const [proposeInstruction, setProposeInstruction] = useState('');
  const [proposeLoading, setProposeLoading] = useState(false);
  const [selectedChange, setSelectedChange] = useState(null);

  useEffect(() => {
    loadTicket();
    loadProposedChanges();
  }, [id]);

  const loadProposedChanges = async () => {
    try {
      const response = await api.getTicketProposedChanges(id);
      setProposedChanges(response.changes || []);
    } catch (err) {
      console.error('Failed to load proposed changes:', err);
    }
  };

  const loadTicket = async () => {
    setLoading(true);
    try {
      const response = await api.getTicket(id);
      setTicket(response.ticket);
    } catch (err) {
      setError('Failed to load ticket');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAIResolve = async () => {
    setAiLoading(true);
    try {
      const response = await api.triggerAIResolution(id);
      if (response.status === 'success') {
        loadTicket();
      }
    } catch (err) {
      console.error('AI resolution failed:', err);
    } finally {
      setAiLoading(false);
    }
  };

  const handleAIAction = async (action, message = '') => {
    try {
      const response = await api.ticketAIAction(id, action, message);
      if (action === 'probe' && response.response) {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: response.response
        }]);
      }
      loadTicket();
    } catch (err) {
      console.error('AI action failed:', err);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await api.ticketChat(id, userMessage);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response
      }]);
    } catch (err) {
      console.error('Chat failed:', err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleProposeChange = async (e) => {
    e.preventDefault();
    if (!proposeFilePath.trim() || !proposeInstruction.trim()) return;

    setProposeLoading(true);
    try {
      const response = await api.proposeChange(id, proposeFilePath, proposeInstruction);
      if (response.status === 'proposed') {
        setShowProposeForm(false);
        setProposeFilePath('');
        setProposeInstruction('');
        loadProposedChanges();
      }
    } catch (err) {
      console.error('Failed to propose change:', err);
    } finally {
      setProposeLoading(false);
    }
  };

  const handleAcceptChange = async (changeId) => {
    try {
      await api.acceptProposedChange(changeId);
      loadProposedChanges();
      setSelectedChange(null);
    } catch (err) {
      console.error('Failed to accept change:', err);
    }
  };

  const handleRejectChange = async (changeId) => {
    try {
      await api.rejectProposedChange(changeId);
      loadProposedChanges();
      setSelectedChange(null);
    } catch (err) {
      console.error('Failed to reject change:', err);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      bug: '#e53e3e',
      feature: '#3182ce',
      task: '#805ad5',
      improvement: '#38a169'
    };
    return colors[category] || '#666';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      critical: '#e53e3e',
      high: '#ed8936',
      medium: '#ecc94b',
      low: '#48bb78'
    };
    return colors[priority] || '#666';
  };

  const getStatusColor = (status) => {
    const colors = {
      open: '#3182ce',
      in_progress: '#ed8936',
      resolved: '#38a169',
      closed: '#718096'
    };
    return colors[status] || '#666';
  };

  if (loading) {
    return (
      <div className="ticket-detail-page">
        <Navigation />
        <main className="ticket-content">
          <div className="loading">Loading ticket...</div>
        </main>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="ticket-detail-page">
        <Navigation />
        <main className="ticket-content">
          <div className="error">{error || 'Ticket not found'}</div>
          <button onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
        </main>
      </div>
    );
  }

  return (
    <div className="ticket-detail-page">
      <Navigation />

      <main className="ticket-content">
        <button className="back-button" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>

        <div className="ticket-header">
          <div className="ticket-badges">
            <span className="badge category" style={{ background: getCategoryColor(ticket.category) }}>
              {ticket.category}
            </span>
            <span className="badge priority" style={{ background: getPriorityColor(ticket.priority) }}>
              {ticket.priority}
            </span>
            <span className="badge status" style={{ background: getStatusColor(ticket.status) }}>
              {ticket.status.replace('_', ' ')}
            </span>
          </div>
          <h1>{ticket.title}</h1>
        </div>

        <section className="ticket-section">
          <h2>Description</h2>
          <p>{ticket.description || 'No description provided'}</p>
        </section>

        <section className="ticket-section">
          <h2>Details</h2>
          <div className="details-grid">
            <div className="detail-item">
              <label>Created</label>
              <span>{new Date(ticket.created_at).toLocaleString()}</span>
            </div>
            <div className="detail-item">
              <label>Updated</label>
              <span>{new Date(ticket.updated_at).toLocaleString()}</span>
            </div>
            <div className="detail-item">
              <label>Creator</label>
              <span>{ticket.creator_username || 'Unknown'}</span>
            </div>
            <div className="detail-item">
              <label>Assignee</label>
              <span>{ticket.assignee_username || 'Unassigned'}</span>
            </div>
            <div className="detail-item">
              <label>Project</label>
              <span>{ticket.project_title || 'No project'}</span>
            </div>
          </div>
        </section>

        <section className="ticket-section ai-section">
          <h2>AI Resolution</h2>

          {!ticket.ai_suggestion ? (
            <div className="ai-empty">
              <p>No AI suggestion yet. Trigger AI to analyze this ticket.</p>
              <button
                className="ai-button primary"
                onClick={handleAIResolve}
                disabled={aiLoading}
              >
                {aiLoading ? 'Analyzing...' : 'Trigger AI Resolution'}
              </button>
            </div>
          ) : (
            <div className="ai-suggestion">
              <div className="suggestion-header">
                <span className={`suggestion-status ${ticket.ai_suggestion_status}`}>
                  {ticket.ai_suggestion_status || 'pending'}
                </span>
                {ticket.ai_files_analyzed && ticket.ai_files_analyzed.length > 0 && (
                  <span className="files-analyzed">
                    {ticket.ai_files_analyzed.length} files analyzed
                  </span>
                )}
              </div>

              <div className="suggestion-content">
                <pre>{ticket.ai_suggestion}</pre>
              </div>

              {ticket.ai_files_analyzed && ticket.ai_files_analyzed.length > 0 && (
                <div className="files-list">
                  <h4>Files Analyzed:</h4>
                  <ul>
                    {ticket.ai_files_analyzed.map((file, i) => (
                      <li key={i}>{file}</li>
                    ))}
                  </ul>
                </div>
              )}

              {ticket.ai_suggestion_status === 'pending' && (
                <div className="ai-actions">
                  <button
                    className="ai-button accept"
                    onClick={() => handleAIAction('accept')}
                  >
                    Accept
                  </button>
                  <button
                    className="ai-button reject"
                    onClick={() => handleAIAction('reject')}
                  >
                    Reject
                  </button>
                  <button
                    className="ai-button probe"
                    onClick={() => setShowChat(true)}
                  >
                    Probe More
                  </button>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="ticket-section proposed-section">
          <div className="section-header">
            <h2>Proposed Code Changes</h2>
            <button
              className="ai-button primary small"
              onClick={() => setShowProposeForm(!showProposeForm)}
            >
              {showProposeForm ? 'Cancel' : '+ Propose Change'}
            </button>
          </div>

          {showProposeForm && (
            <form className="propose-form" onSubmit={handleProposeChange}>
              <div className="form-group">
                <label>File Path</label>
                <input
                  type="text"
                  value={proposeFilePath}
                  onChange={(e) => setProposeFilePath(e.target.value)}
                  placeholder="e.g., app/routes/auth.py"
                  required
                />
              </div>
              <div className="form-group">
                <label>Change Instruction</label>
                <textarea
                  value={proposeInstruction}
                  onChange={(e) => setProposeInstruction(e.target.value)}
                  placeholder="Describe what changes to make..."
                  rows={3}
                  required
                />
              </div>
              <button type="submit" className="ai-button primary" disabled={proposeLoading}>
                {proposeLoading ? 'Generating...' : 'Generate Proposed Change'}
              </button>
            </form>
          )}

          {proposedChanges.length === 0 ? (
            <p className="empty-text">No proposed changes yet.</p>
          ) : (
            <div className="proposed-list">
              {proposedChanges.map(change => (
                <div key={change.id} className={`proposed-item ${change.status}`}>
                  <div className="proposed-header">
                    <span className="file-path">{change.file_path}</span>
                    <span className={`status-badge ${change.status}`}>{change.status}</span>
                  </div>
                  <p className="change-desc">{change.change_description}</p>
                  {change.status === 'pending' && (
                    <div className="proposed-actions">
                      <button
                        className="ai-button small"
                        onClick={() => setSelectedChange(selectedChange === change.id ? null : change.id)}
                      >
                        {selectedChange === change.id ? 'Hide Diff' : 'View Diff'}
                      </button>
                      <button
                        className="ai-button accept small"
                        onClick={() => handleAcceptChange(change.id)}
                      >
                        Accept
                      </button>
                      <button
                        className="ai-button reject small"
                        onClick={() => handleRejectChange(change.id)}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                  {selectedChange === change.id && (
                    <div className="diff-view">
                      <div className="diff-panel">
                        <h4>Original</h4>
                        <pre>{change.original_content}</pre>
                      </div>
                      <div className="diff-panel proposed">
                        <h4>Proposed</h4>
                        <pre>{change.proposed_content}</pre>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {showChat && (
          <section className="ticket-section chat-section">
            <h2>Chat with AI</h2>
            <div className="chat-messages">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="chat-message assistant">
                  <div className="message-content typing">Thinking...</div>
                </div>
              )}
            </div>
            <form className="chat-input" onSubmit={handleChatSubmit}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a follow-up question..."
                disabled={chatLoading}
              />
              <button type="submit" disabled={chatLoading || !chatInput.trim()}>
                Send
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );
};

export default TicketDetailPage;
