import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { fileService } from '../../services/api';
import './Files.css';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleFileSelect = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication token is missing. Please log in again.');
        navigate('/login');
        return;
      }

      await fileService.uploadFile(formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });
      
      setSuccess('File uploaded successfully!');
      setTimeout(() => {
        navigate('/files');
      }, 1500);
      
    } catch (err) {
      console.error('Upload error:', err);
      if (err.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
        navigate('/login');
      } else {
        setError(err.response?.data?.detail || 'Error uploading file. Please try again.');
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="upload-container">
      <div className="upload-wrapper">
        {/* Header */}
        <div className="upload-header">
          <Link to="/files" className="upload-back-btn">
            ← Back
          </Link>
          <div className="upload-title-section">
            <h1 className="upload-main-title">📤 Upload File</h1>
            <p className="upload-subtitle">Upload your CSV or Excel files to Smart Stock</p>
          </div>
        </div>

        {/* Main Upload Card */}
        <div className="upload-card">
          {/* Alerts */}
          {error && (
            <div className="upload-error-alert">
              ❌ {error}
            </div>
          )}
          
          {success && (
            <div className="upload-success-alert">
              ✅ {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="upload-form">
            {/* Drag & Drop Area */}
            <div className="upload-section">
              <label className="upload-label">Select File</label>
              
              <div
                className={`upload-drop-zone ${dragActive ? 'upload-drop-active' : ''} ${file ? 'upload-drop-success' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input').click()}
              >
                <input
                  id="file-input"
                  type="file"
                  onChange={handleFileSelect}
                  accept=".csv,.xlsx,.xls"
                  className="upload-file-input"
                />

                {file ? (
                  <div className="upload-file-selected">
                    <div className="upload-file-icon">📄</div>
                    <h3 className="upload-file-name">{file.name}</h3>
                    <p className="upload-file-size">{formatFileSize(file.size)}</p>
                    <p className="upload-file-status">✓ File ready for upload</p>
                  </div>
                ) : (
                  <div className="upload-file-empty">
                    <div className="upload-cloud-icon">☁️</div>
                    <h3 className="upload-empty-title">
                      Drop your file here or click to browse
                    </h3>
                    <p className="upload-empty-subtitle">
                      Supports CSV, XLSX, XLS files up to 10MB
                    </p>
                    <div className="upload-file-types">
                      <span className="upload-file-type">.CSV</span>
                      <span className="upload-file-type">.XLSX</span>
                      <span className="upload-file-type">.XLS</span>
                    </div>
                  </div>
                )}

                {dragActive && (
                  <div className="upload-drag-overlay">
                    <p className="upload-drag-text">Drop file here!</p>
                  </div>
                )}
              </div>

              {file && (
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="upload-remove-btn"
                >
                  ❌ Remove file
                </button>
              )}
            </div>

            {/* Progress Bar */}
            {uploading && (
              <div className="upload-progress-section">
                <div className="upload-progress-header">
                  <span className="upload-progress-label">Upload Progress</span>
                  <span className="upload-progress-percent">{uploadProgress}%</span>
                </div>
                <div className="upload-progress-container">
                  <div
                    className="upload-progress-bar"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="upload-actions">
              <Link to="/files" className="upload-cancel-btn">
                ← Back to Files
              </Link>

              <button
                type="submit"
                disabled={!file || uploading}
                className={`upload-submit-btn ${!file || uploading ? 'upload-submit-disabled' : ''}`}
              >
                {uploading ? (
                  <>
                    <div className="upload-spinner"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    📤 Upload File
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;