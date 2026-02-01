import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import api from '../services/api';
import './FileBrowserPage.css';

const FileBrowserPage = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [fileLoading, setFileLoading] = useState(false);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await api.getFiles();
      setFiles(response.files || []);
    } catch (err) {
      setError('Failed to load files');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (file) => {
    setSelectedFile(file);
    setFileLoading(true);
    try {
      const response = await api.readFile(file.path);
      setFileContent(response.content || '');
    } catch (err) {
      setFileContent('Failed to load file content');
      console.error(err);
    } finally {
      setFileLoading(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="file-browser-page">
      <Navigation />

      <main className="file-browser-content">
        <h1>File Browser</h1>

        <div className="file-browser-layout">
          <div className="file-list-panel">
            <h2>Files</h2>
            {loading ? (
              <div className="loading">Loading files...</div>
            ) : error ? (
              <div className="error">{error}</div>
            ) : files.length === 0 ? (
              <div className="empty">No files found</div>
            ) : (
              <ul className="file-list">
                {files.map((file, i) => (
                  <li
                    key={i}
                    className={`file-item ${selectedFile?.path === file.path ? 'selected' : ''}`}
                    onClick={() => handleFileClick(file)}
                  >
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">{formatSize(file.size)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="file-content-panel">
            {selectedFile ? (
              <>
                <div className="file-header">
                  <h2>{selectedFile.name}</h2>
                  <span className="file-path">{selectedFile.path}</span>
                </div>
                {fileLoading ? (
                  <div className="loading">Loading content...</div>
                ) : (
                  <pre className="file-content">{fileContent}</pre>
                )}
              </>
            ) : (
              <div className="empty-content">
                <p>Select a file to view its content</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default FileBrowserPage;
