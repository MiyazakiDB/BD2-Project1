import React, { useState, useEffect } from 'react';
import { Table, Button, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { fileService } from '../../services/api';

const FileList = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fileService.listFiles();
      setFiles(response.data);
    } catch (err) {
      setError('Error loading files. Please try again.');
      console.error(err);
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

  if (loading) return <div className="text-center mt-5">Loading files...</div>;

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>My Files</h2>
        <Button as={Link} to="/files/upload" variant="primary">
          Upload New File
        </Button>
      </div>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      {files.length === 0 ? (
        <Alert variant="info">You don't have any files yet. Upload your first file!</Alert>
      ) : (
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Size</th>
              <th>Upload Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.filename}>
                <td>{file.filename}</td>
                <td>{Math.round(file.size / 1024)} KB</td>
                <td>{new Date(file.upload_date).toLocaleString()}</td>
                <td>
                  <Button 
                    variant="danger" 
                    size="sm"
                    onClick={() => handleDelete(file.filename)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
};

export default FileList;
