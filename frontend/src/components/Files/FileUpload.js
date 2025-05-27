import React, { useState } from 'react';
import { Form, Button, Alert, ProgressBar } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { fileService } from '../../services/api';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
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
      
      navigate('/files');
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
    }
  };

  return (
    <div className="mt-4">
      <h2>Upload File</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Select File</Form.Label>
          <Form.Control 
            type="file" 
            onChange={handleFileChange}
            disabled={uploading}
          />
        </Form.Group>

        {uploading && (
          <ProgressBar 
            now={uploadProgress} 
            label={`${uploadProgress}%`} 
            className="mb-3" 
          />
        )}

        <div className="d-flex justify-content-between">
          <Button 
            variant="secondary" 
            onClick={() => navigate('/files')}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button 
            variant="primary" 
            type="submit"
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      </Form>
    </div>
  );
};

export default FileUpload;
