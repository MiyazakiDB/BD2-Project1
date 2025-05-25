import React, { useState, useEffect } from 'react';
import { Table, Button, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { fileService } from '../../services/api';

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
    if (window.confirm(`Are you sure you want to delete ${filename}?`)) {
      try {
        await fileService.deleteFile(filename);
        fetchFiles();
      } catch (err) {
        setError('Error deleting file. Please try again.');
        console.error(err);
      }
    }
  };

  return (
    <div className="container fade-in">
      <div className="smart-header">
        <h1>Smart Stock Files</h1>
        <p>Manage your uploaded data files</p>
      </div>

      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 style={{color: '#1e3a8a', margin: 0}}>My Files</h2>
        <Link to="/files/upload" className="btn btn-primary">
          📁 Upload New File
        </Link>
      </div>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading your files...</p>
        </div>
      ) : files.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📂</div>
          <h3>No files found</h3>
          <p>Upload your first data file to get started with Smart Stock</p>
          <Link to="/files/upload" className="btn btn-primary">
            Upload Your First File
          </Link>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            📁 Files Library ({files.length} files)
          </div>
          <div className="card-body" style={{padding: 0}}>
            <Table className="table">
              <thead>
                <tr>
                  <th>📄 Filename</th>
                  <th>📊 Size</th>
                  <th>📅 Upload Date</th>
                  <th>⚡ Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file, index) => (
                  <tr key={file.filename} className="slide-in-left" style={{animationDelay: `${index * 0.1}s`}}>
                    <td style={{fontWeight: '500'}}>{file.filename}</td>
                    <td>{Math.round(file.size / 1024)} KB</td>
                    <td>{new Date(file.upload_date).toLocaleString()}</td>
                    <td>
                      <Button 
                        variant="danger" 
                        size="sm"
                        onClick={() => handleDelete(file.filename)}
                        className="btn-sm"
                      >
                        🗑️ Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileList;