import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { fileService } from '../../services/api';
import './Files.css';

const FileList = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fileService.listFiles();
      setFiles(response.data);
      setError('');
    } catch (err) {
      console.error('Error loading files:', err);
      
      if (err.response?.status === 401) {
        setError('Tu sesión ha expirado. Por favor inicia sesión nuevamente.');
        
        const token = localStorage.getItem('token');
        if (token) {
          localStorage.removeItem('token');
          setTimeout(() => navigate('/login'), 2000);
        }
      } else {
        setError('Error cargando archivos. Por favor intenta de nuevo.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleDelete = async (filename) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar ${filename}?`)) {
      try {
        await fileService.deleteFile(filename);
        fetchFiles();
      } catch (err) {
        setError('Error eliminando archivo. Por favor intenta de nuevo.');
        console.error(err);
      }
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
    <div className="files-container">
      <div className="files-wrapper">
        {/* Header */}
        <div className="files-header">
          <div className="files-header-content">
            <div className="files-title-section">
              <h1 className="files-main-title">📁 File Manager</h1>
              <p className="files-subtitle">Manage your uploaded data files with ease</p>
            </div>
            <Link to="/files/upload" className="files-upload-btn">
              📤 Upload New File
            </Link>
          </div>

          {/* Stats Cards */}
          <div className="files-stats-grid">
            <div className="files-stat-card">
              <div className="files-stat-icon">📄</div>
              <div className="files-stat-info">
                <p className="files-stat-label">Total Files</p>
                <p className="files-stat-value">{files.length}</p>
              </div>
            </div>
            
            <div className="files-stat-card">
              <div className="files-stat-icon">💾</div>
              <div className="files-stat-info">
                <p className="files-stat-label">Total Size</p>
                <p className="files-stat-value">
                  {formatFileSize(files.reduce((acc, file) => acc + file.size, 0))}
                </p>
              </div>
            </div>

            <div className="files-stat-card">
              <div className="files-stat-icon">📅</div>
              <div className="files-stat-info">
                <p className="files-stat-label">Last Upload</p>
                <p className="files-stat-value">{files.length > 0 ? 'Today' : 'None'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="files-error-alert">
            ❌ {error}
          </div>
        )}

        {/* Loading State chuta */}
        {loading ? (
          <div className="files-loading-container">
            <div className="files-loading-spinner"></div>
            <p className="files-loading-text">Loading your files...</p>
          </div>
        ) : files.length === 0 ? (
          /* Empty State */
          <div className="files-empty-state">
            <div className="files-empty-icon">📂</div>
            <h3 className="files-empty-title">No files found</h3>
            <p className="files-empty-subtitle">Upload your first data file to get started</p>
            <Link to="/files/upload" className="files-empty-upload-btn">
              📤 Upload Your First File
            </Link>
          </div>
        ) : (
          /* Files Grid */
          <div className="files-grid">
            {files.map((file, index) => (
              <div
                key={file.filename}
                className="files-card"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="files-card-header">
                  <div className="files-card-icon">📄</div>
                  <button
                    onClick={() => handleDelete(file.filename)}
                    className="files-delete-btn"
                  >
                    🗑️
                  </button>
                </div>
                
                <h3 className="files-card-title">{file.filename}</h3>
                
                <div className="files-card-details">
                  <div className="files-card-detail">
                    <span>Size:</span>
                    <span>{formatFileSize(file.size)}</span>
                  </div>
                  <div className="files-card-detail">
                    <span>Uploaded:</span>
                    <span>{new Date(file.upload_date).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="files-card-progress">
                  <div className="files-progress-bar"></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileList;