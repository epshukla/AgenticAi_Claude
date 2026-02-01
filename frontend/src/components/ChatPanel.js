import React, { useState, useRef, useEffect } from 'react';
import './ChatPanel.css';

function ChatPanel({
  messages,
  selectedFile,
  onSendChat,
  onModifyFile,
  onClearHistory,
  onProcessTask,
  loading
}) {
  const [chatMessage, setChatMessage] = useState('');
  const [instruction, setInstruction] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendChat = (e) => {
    e.preventDefault();
    if (chatMessage.trim() && !loading) {
      onSendChat(chatMessage);
      setChatMessage('');
    }
  };

  const handleModifyFile = () => {
    if (selectedFile && instruction.trim() && !loading) {
      onModifyFile(selectedFile, instruction);
      setInstruction('');
    }
  };

  const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h3>Chat with Claude</h3>
        <button
          className="clear-btn"
          onClick={onClearHistory}
          disabled={loading}
        >
          Clear History
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>Select a file and provide instructions to modify it,</p>
            <p>or start a general conversation with Claude.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.type}`}>
              <div className="message-header">
                {msg.type === 'user' && '👤 You'}
                {msg.type === 'assistant' && '🤖 Claude'}
                {msg.type === 'system' && '⚙️ System'}
              </div>
              <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: escapeHtml(msg.content).replace(/\n/g, '<br>') }}
              />
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <div className="task-section">
          <div className="section-label">Smart Task (analyzes only relevant files)</div>
          <textarea
            className="task-input"
            placeholder="Describe what you want to do... e.g., 'Find all API endpoints and list their routes'"
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            disabled={loading}
          />
          <button
            className="task-btn"
            onClick={() => {
              if (taskDescription.trim() && !loading) {
                onProcessTask(taskDescription);
                setTaskDescription('');
              }
            }}
            disabled={!taskDescription.trim() || loading}
          >
            {loading ? 'Processing...' : 'Run Smart Task'}
          </button>
        </div>

        {selectedFile && (
          <div className="modify-section">
            <div className="selected-file">
              📄 Selected: <strong>{selectedFile}</strong>
            </div>
            <textarea
              className="instruction-input"
              placeholder="Enter instructions for Claude to modify this file..."
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              disabled={loading}
            />
            <button
              className="modify-btn"
              onClick={handleModifyFile}
              disabled={!instruction.trim() || loading}
            >
              {loading ? 'Processing...' : 'Modify File'}
            </button>
          </div>
        )}

        <form className="chat-form" onSubmit={handleSendChat}>
          <input
            type="text"
            className="chat-input"
            placeholder="Send a message to Claude..."
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!chatMessage.trim() || loading}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatPanel;
