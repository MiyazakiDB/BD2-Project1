import React, { useState } from 'react';
import { Form, Button, Alert, Card, Row, Col, Badge } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
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
    formData.append('has_headers', hasHeaders.toString()); // Agregar información de encabezados
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

  return (
    <div className="mt-4">
      <h2>Create New Table</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Card>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-4">
              <Form.Label>Table Name</Form.Label>
              <Form.Control
                type="text"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                placeholder="Enter table name"
                required
              />
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Label>File Upload</Form.Label>
              <Form.Control
                type="file"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                required
              />
            </Form.Group>

            {/* Nuevo campo para especificar si tiene encabezados */}
            <Form.Group className="mb-4">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <Form.Label className="mb-0">File Header Settings</Form.Label>
                <Badge bg={hasHeaders ? 'success' : 'secondary'} pill>
                  {hasHeaders ? 'Headers: YES' : 'Headers: NO'}
                </Badge>
              </div>
              <Form.Check
                type="checkbox"
                label="File has headers (first line contains column names)"
                checked={hasHeaders}
                onChange={(e) => setHasHeaders(e.target.checked)}
              />
              <Form.Text className="text-muted">
                {hasHeaders 
                  ? "The first line will be skipped as it contains column names." 
                  : "All lines will be processed as data rows."}
              </Form.Text>
            </Form.Group>

            <h5 className="mb-3">Columns</h5>
            
            {columns.map((column, index) => (
              <Card className="mb-3" key={index}>
                <Card.Body>
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
                    <Col md={4}>
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
                    <Col md={1} className="d-flex align-items-center justify-content-end">
                      {columns.length > 1 && (
                        <Button 
                          variant="outline-danger" 
                          size="sm"
                          onClick={() => removeColumn(index)}
                        >
                          Remove
                        </Button>
                      )}
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            ))}

            <div className="mb-4">
              <Button variant="outline-primary" onClick={addColumn}>
                Add Column
              </Button>
            </div>

            <div className="d-flex justify-content-between">
              <Button 
                variant="secondary" 
                onClick={() => navigate('/tables')}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button 
                variant="primary" 
                type="submit"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Table'}
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
};

export default CreateTable;
