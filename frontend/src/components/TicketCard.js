import React from 'react';
import './TicketCard.css';

const TicketCard = ({ ticket, onClick }) => {
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

  const truncateDescription = (text, maxLength = 100) => {
    if (!text) return 'No description';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="ticket-card" onClick={onClick}>
      <div className="ticket-card-header">
        <span
          className="category-badge"
          style={{ background: getCategoryColor(ticket.category) }}
        >
          {ticket.category}
        </span>
        <span
          className="priority-badge"
          style={{ background: getPriorityColor(ticket.priority) }}
        >
          {ticket.priority}
        </span>
        {ticket.project_title && (
          <span className="project-badge">
            {ticket.project_title}
          </span>
        )}
      </div>

      <h3 className="ticket-card-title">{ticket.title}</h3>

      <p className="ticket-card-description">
        {truncateDescription(ticket.description)}
      </p>

      <div className="ticket-card-footer">
        <span
          className="status-badge"
          style={{ background: getStatusColor(ticket.status) }}
        >
          {ticket.status.replace('_', ' ')}
        </span>

        {ticket.ai_suggestion && (
          <span className="ai-indicator" title="AI suggestion available">
            AI
          </span>
        )}
      </div>
    </div>
  );
};

export default TicketCard;
