import React, { useState } from 'react';
import { Form, Button, Alert, Table, Card } from 'react-bootstrap';
import { queryService } from '../../services/api';

const QueryExecutor = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [executionTime, setExecutionTime] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query to execute');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);
    setExecutionTime(null);

    try {
      const startTime = performance.now();
      const response = await queryService.executeQuery(query);
      const endTime = performance.now();
      
      setResults(response.data);
      setExecutionTime(endTime - startTime);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error executing query. Please check syntax and try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderResults = () => {
    if (!results) return null;

    if (results.rows && results.rows.length > 0) {
      // Display as table
      return (
        <div className="mt-4">
          <h4>Results ({results.rows.length} rows)</h4>
          <Table striped bordered hover size="sm">
            <thead>
              <tr>
                {Object.keys(results.rows[0]).map(key => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.rows.map((row, index) => (
                <tr key={index}>
                  {Object.values(row).map((value, i) => (
                    <td key={i}>{value !== null ? String(value) : 'NULL'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      );
    } else if (results.message) {
      // Display message for DDL/DML operations
      return (
        <Alert variant="success" className="mt-4">
          {results.message}
        </Alert>
      );
    }
    
    return (
      <Alert variant="info" className="mt-4">
        Query executed successfully. No results to display.
      </Alert>
    );
  };

  return (
    <div className="mt-4">
      <h2>Query Executor</h2>
      
      <Card>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Enter SQL Query</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="SELECT * FROM table_name;"
              />
            </Form.Group>

            <Button 
              variant="primary" 
              type="submit"
              disabled={loading}
            >
              {loading ? 'Executing...' : 'Execute Query'}
            </Button>
          </Form>
        </Card.Body>
      </Card>

      {error && <Alert variant="danger" className="mt-4">{error}</Alert>}
      
      {executionTime !== null && (
        <Alert variant="info" className="mt-4">
          Query executed in {executionTime.toFixed(2)} ms
        </Alert>
      )}

      {renderResults()}
    </div>
  );
};

export default QueryExecutor;
