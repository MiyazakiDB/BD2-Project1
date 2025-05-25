import React, { useState } from 'react';
import { Form, Button, Alert, ProgressBar } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { fileService } from '../../services/api';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

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
      // Verify token presence before making request
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

  return (
    <div className="container fade-in">
      <div className="smart-header">
        <h1>Upload Data File</h1>
        <p>Upload your CSV or Excel files to Smart Stock</p>
      </div>

      <div className="card">
        <div className="card-header">
          📤 File Upload
        </div>
        <div className="card-body">
          {error && <Alert variant="danger">{error}</Alert>}
          {success && <Alert variant="success">{success}</Alert>}
          
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-4">
              <Form.Label>Select File</Form.Label>
              <div 
                className={`file-upload-area ${dragActive ? 'dragover' : ''}`}
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
                  style={{ display: 'none' }}
                />
                {file ? (
                  <div style={{textAlign: 'center'}}>
                    <div style={{fontSize: '2rem', marginBottom: '10px'}}>📄</div>
                    <p style={{margin: 0, fontWeight: '500'}}>{file.name}</p>
                    <p style={{margin: 0, color: '#64748b', fontSize: '0.9rem'}}>
                      {Math.round(file.size / 1024)} KB
                    </p>
                  </div>
                ) : (
                  <div style={{textAlign: 'center'}}>
                    <div style={{fontSize: '3rem', marginBottom: '15px'}}>☁️</div>
                    <p style={{margin: 0, fontWeight: '500'}}>Drop your file here or click to browse</p>
                    <p style={{margin: '5px 0 0 0', color: '#64748b', fontSize: '0.9rem'}}>
                      Supports CSV, XLSX, XLS files
                    </p>
                  </div>
                )}
              </div>
            </Form.Group>

            {uploading && (
              <Form.Group className="mb-3">
                <Form.Label>Upload Progress</Form.Label>
                <ProgressBar 
                  now={uploadProgress} 
                  label={`${uploadProgress}%`}
                  variant="info"
                  style={{height: '20px'}}
                />
              </Form.Group>
            )}

            <div className="d-flex justify-content-between">
              <Link to="/files" className="btn btn-secondary">
                ← Back to Files
              </Link>
              <Button 
                variant="primary" 
                type="submit" 
                disabled={!file || uploading}
              >
                {uploading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Uploading...
                  </>
                ) : (
                  '📤 Upload File'
                )}
              </Button>
            </div>
          </Form>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;