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
      console.log('=== STARTING QUERY EXECUTION ===');
      console.log('Query to execute:', query);
      
      const response = await queryService.executeQuery(query);
      
      console.log('=== RAW RESPONSE FROM API SERVICE ===');
      console.log('Full response:', response);
      console.log('Response type:', typeof response);
      console.log('Response keys:', Object.keys(response || {}));
      console.log('Response.columns:', response?.columns);
      console.log('Response.data:', response?.data);
      console.log('=== END RESPONSE ANALYSIS ===');
      
      // CORRECCIÓN: response ya es el objeto correcto
      setResults(response);  // ✅ Usar response directamente
      setExecutionTime(response?.execution_time_ms || 0);
      
    } catch (err) {
      console.error('=== QUERY EXECUTION ERROR ===');
      console.error('Error object:', err);
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      console.error('=== END ERROR ===');
      
      setError(err.response?.data?.detail || err.message || 'Error executing query. Please check syntax and try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderResults = () => {
    console.log('=== RENDERING RESULTS ===');
    console.log('Results state:', results);
    console.log('Results type:', typeof results);
    console.log('Results keys:', Object.keys(results || {}));
    
    if (!results) {
      console.log('No results to render');
      return null;
    }

    // ✅ CORRECCIÓN: Verificar el formato correcto del backend
    if (results.data && Array.isArray(results.data) && results.data.length > 0) {
      console.log('Rendering table with backend format');
      console.log('Columns:', results.columns);
      console.log('Data rows:', results.data);
      console.log('Number of rows:', results.data.length);
      
      return (
        <div className="mt-4">
          <h4>Results ({results.data.length} rows)</h4>
          <Table striped bordered hover size="sm">
            <thead>
              <tr>
                {results.columns && results.columns.map((col, index) => (
                  <th key={index}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell !== null ? String(cell) : 'NULL'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
          <small className="text-muted">
            Rows affected: {results.rows_affected || results.data.length} | 
            Execution time: {results.execution_time_ms?.toFixed(2) || 0} ms
          </small>
        </div>
      );
    }
    
    // Verificar formato legacy (si existiera)
    else if (results.rows && results.rows.length > 0) {
      console.log('Rendering table with legacy format');
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
    }
    
    // Verificar si hay mensaje de operación
    else if (results.message) {
      console.log('Rendering message:', results.message);
      return (
        <Alert variant="success" className="mt-4">
          {results.message}
        </Alert>
      );
    }
    
    // Si llegamos aquí, no hay datos para mostrar
    else {
      console.log('No data to display');
      console.log('Results structure:', {
        hasData: !!results.data,
        dataLength: results.data?.length,
        hasRows: !!results.rows,
        hasMessage: !!results.message
      });
      
      return (
        <Alert variant="info" className="mt-4">
          Query executed successfully. No results to display.
          <br />
          <small>Debug: {JSON.stringify(results, null, 2)}</small>
        </Alert>
      );
    }
  };

  return (
    <div className="container fade-in">
      <div className="smart-header">
        <h1>Smart Stock</h1>
        <p>Advanced Database Query System</p>
      </div>
      
      <div className="mt-4">
        <Card>
          <div className="card-header">Query Executor</div>
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
    </div>
  );
};

export default QueryExecutor;
