import React, { useState } from 'react';
import { Form, Button, Alert, Card, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { tableService } from '../../services/api';

const CreateTable = () => {
  const navigate = useNavigate();
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState([{ name: '', data_type: 'INT', is_indexed: false }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
    
    // Basic validation
    if (!tableName.trim()) {
      setError('Table name is required');
      return;
    }

    const invalidColumns = columns.filter(col => !col.name.trim());
    if (invalidColumns.length > 0) {
      setError('All columns must have names');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await tableService.createTable({
        name: tableName,
        columns: columns
      });
      navigate('/tables');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating table. Please try again.');
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
