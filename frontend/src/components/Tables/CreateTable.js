import React, { useState } from 'react';
import { Form, Button, Alert, Card, Row, Col, Badge } from 'react-bootstrap';
import { Link,useNavigate } from 'react-router-dom';
import { tableService } from '../../services/api';

const CreateTable = () => {
  const navigate = useNavigate();
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState([{ name: '', data_type: 'INT', is_indexed: false }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [hasHeaders, setHasHeaders] = useState(true); // Nuevo estado para encabezados

  const dataTypes = ['INT', 'FLOAT', 'VARCHAR', 'BOOLEAN', 'DATE'];

  const handleColumnChange = (index, field, value) => {
    const newColumns = [...columns];
    newColumns[index][field] = value;
    setColumns(newColumns);
  };

  const addColumn = () => {
    setColumns([...columns, { name: '', data_type: 'INT', is_indexed: false }]);
  };

  const removeColumn = (index) => {
    if (columns.length > 1) {
      const newColumns = columns.filter((_, i) => i !== index);
      setColumns(newColumns);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!tableName.trim()) {
      setError('Table name is required');
      return;
    }

    if (!selectedFile) {
      setError('File is required');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('table_name', tableName);
    formData.append('has_headers', hasHeaders.toString()); // Enviar información de encabezados
    formData.append(
      'columns',
      JSON.stringify(
        columns.map((col) => ({
          name: col.name,
          data_type: col.data_type,
          size: col.data_type === 'VARCHAR' ? col.size || 255 : null,
          index_type: col.is_indexed ? col.index_type || 'BTREE' : null,
        }))
      )
    );

    try {
      await tableService.createTable(formData);
      navigate('/tables');
    } catch (err) {
      const errorDetail = err.response?.data?.detail;

      if (Array.isArray(errorDetail)) {
        setError(errorDetail.map((e) => e.msg).join(', '));
      } else if (typeof errorDetail === 'string') {
        setError(errorDetail);
      } else {
        setError('Error creating table. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Mantén toda la lógica existente, solo cambia el return:

return (
  <div className="container fade-in">
    <div className="smart-header">
      <h1>Create New Table</h1>
      <p>Define your table structure and upload data</p>
    </div>

    <div className="card">
      <div className="card-header">
        🏗️ Table Configuration
      </div>
      <div className="card-body">
        {error && <Alert variant="danger">{error}</Alert>}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-4">
            <Form.Label>Table Name</Form.Label>
            <Form.Control
              type="text"
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              placeholder="Enter table name (e.g., products, customers)"
              required
            />
          </Form.Group>

          <Form.Group className="mb-4">
            <Form.Label>Data File</Form.Label>
            <Form.Control
              type="file"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              accept=".csv,.xlsx,.xls"
              required
            />
            <Form.Text className="text-muted">
              Upload CSV, XLSX, or XLS files with your data
            </Form.Text>
          </Form.Group>

          <Form.Group className="mb-4">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <Form.Label className="mb-0">File Header Settings</Form.Label>
              <span className={`badge ${hasHeaders ? 'bg-success' : 'bg-secondary'}`}>
                {hasHeaders ? 'Headers: YES' : 'Headers: NO'}
              </span>
            </div>
            <Form.Check
              type="checkbox"
              label="File has headers (first line contains column names)"
              checked={hasHeaders}
              onChange={(e) => setHasHeaders(e.target.checked)}
            />
          </Form.Group>

          <div className="mb-4">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5 style={{color: '#1e3a8a', margin: 0}}>Column Definitions</h5>
              <Button variant="secondary" onClick={addColumn} size="sm">
                ➕ Add Column
              </Button>
            </div>
            
            {columns.map((column, index) => (
              <div key={index} className="card-item mb-3">
                <Row>
                  <Col md={4}>
                    <Form.Group className="mb-2">
                      <Form.Label>Column Name</Form.Label>
                      <Form.Control
                        type="text"
                        value={column.name}
                        onChange={(e) => handleColumnChange(index, 'name', e.target.value)}
                        placeholder="Enter column name"
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col md={3}>
                    <Form.Group className="mb-2">
                      <Form.Label>Data Type</Form.Label>
                      <Form.Select
                        value={column.data_type}
                        onChange={(e) => handleColumnChange(index, 'data_type', e.target.value)}
                      >
                        {dataTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={3}>
                    <Form.Group className="mb-2 mt-4">
                      <Form.Check
                        type="checkbox"
                        label="Create Index"
                        checked={column.is_indexed}
                        onChange={(e) => handleColumnChange(index, 'is_indexed', e.target.checked)}
                      />
                    </Form.Group>
                  </Col>
                  <Col md={2} className="d-flex align-items-center justify-content-end">
                    {columns.length > 1 && (
                      <Button 
                        variant="danger" 
                        size="sm"
                        onClick={() => removeColumn(index)}
                      >
                        🗑️
                      </Button>
                    )}
                  </Col>
                </Row>
              </div>
            ))}
          </div>

          <div className="d-flex justify-content-between">
            <Link to="/tables" className="btn btn-secondary">
              ← Back to Tables
            </Link>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Creating...
                </>
              ) : (
                '🏗️ Create Table'
              )}
            </Button>
          </div>
        </Form>
      </div>
    </div>
  </div>
);
};

export default CreateTable;
