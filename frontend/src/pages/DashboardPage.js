import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import TicketCard from '../components/TicketCard';
import TicketForm from '../components/TicketForm';
import api from '../services/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const navigate = useNavigate();

  const categories = [
    { key: 'all', label: 'All' },
    { key: 'bug', label: 'Bugs' },
    { key: 'feature', label: 'Features' },
    { key: 'task', label: 'Tasks' },
    { key: 'improvement', label: 'Improvements' },
  ];

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const response = await api.getTickets();
      setTickets(response.tickets || []);
    } catch (err) {
      setError('Failed to load tickets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (ticketData) => {
    try {
      await api.createTicket(ticketData);
      setShowForm(false);
      loadTickets();
    } catch (err) {
      console.error('Failed to create ticket:', err);
    }
  };

  const filteredTickets = activeCategory === 'all'
    ? tickets
    : tickets.filter(t => t.category === activeCategory);

  const handleTicketClick = (ticketId) => {
    navigate(`/ticket/${ticketId}`);
  };

  return (
    <div className="dashboard-page">
      <Navigation />

      <main className="dashboard-content">
        <div className="dashboard-header">
          <h1>Tickets Dashboard</h1>
          <button className="create-button" onClick={() => setShowForm(true)}>
            + Create Ticket
          </button>
        </div>

        <div className="category-tabs">
          {categories.map(cat => (
            <button
              key={cat.key}
              className={`category-tab ${activeCategory === cat.key ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.key)}
            >
              {cat.label}
              {cat.key !== 'all' && (
                <span className="count">
                  {tickets.filter(t => t.category === cat.key).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading">Loading tickets...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : filteredTickets.length === 0 ? (
          <div className="empty-state">
            <p>No tickets found</p>
            <button onClick={() => setShowForm(true)}>Create your first ticket</button>
          </div>
        ) : (
          <div className="tickets-grid">
            {filteredTickets.map(ticket => (
              <TicketCard
                key={ticket.id}
                ticket={ticket}
                onClick={() => handleTicketClick(ticket.id)}
              />
            ))}
          </div>
        )}
      </main>

      {showForm && (
        <TicketForm
          onSubmit={handleCreateTicket}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  );
};

export default DashboardPage;
