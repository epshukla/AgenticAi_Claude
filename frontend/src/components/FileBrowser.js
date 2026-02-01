import React from 'react';
import './FileBrowser.css';

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function FileBrowser({ files, selectedFile, onSelectFile, loading }) {
  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <h3>Files</h3>
        <span className="file-count">{files.length} files</span>
      </div>
      <div className="file-list">
        {loading ? (
          <div className="loading">Loading files...</div>
        ) : files.length === 0 ? (
          <div className="no-files">No files found</div>
        ) : (
          files.map((file) => (
            <div
              key={file.path}
              className={`file-item ${selectedFile === file.path ? 'selected' : ''}`}
              onClick={() => onSelectFile(file.path)}
            >
              <div className="file-icon">
                {file.is_dir ? '📁' : '📄'}
              </div>
              <div className="file-info">
                <div className="file-name">{file.name}</div>
                <div className="file-meta">
                  {!file.is_dir && (
                    <>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                      <span className="file-date">
                        {new Date(file.modified * 1000).toLocaleDateString()}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default FileBrowser;
