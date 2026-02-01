import React from 'react';
import './FilePreview.css';

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function FilePreview({ selectedFile, fileContent, fileInfo, loading }) {
  return (
    <div className="file-preview">
      <div className="preview-header">
        <h3>File Preview</h3>
        {fileInfo && (
          <div className="file-stats">
            <span className="file-ext">{fileInfo.extension}</span>
            <span className="file-size">{formatFileSize(fileInfo.size)}</span>
          </div>
        )}
      </div>

      <div className="preview-content">
        {loading ? (
          <div className="preview-placeholder">
            <div className="loading-spinner"></div>
            <p>Loading file...</p>
          </div>
        ) : selectedFile ? (
          fileContent ? (
            <pre className="code-preview">{fileContent}</pre>
          ) : (
            <div className="preview-placeholder">
              <p>Unable to load file content</p>
            </div>
          )
        ) : (
          <div className="preview-placeholder">
            <span className="placeholder-icon">📄</span>
            <p>Select a file to preview its contents</p>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="preview-footer">
          <span className="file-path">{selectedFile}</span>
        </div>
      )}
    </div>
  );
}

export default FilePreview;
