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
      
      console.log('=== RAW AXIOS RESPONSE ===');
      console.log('Full Axios response:', response);
      console.log('Response status:', response?.status);
      console.log('Response data type:', typeof response);
      console.log('Response keys:', Object.keys(response || {}));
      
      // Determinar la estructura de datos correcta
      let actualData;
      if (response.data) {
        // Si la respuesta tiene estructura de Axios (response.data)
        actualData = response.data;
        console.log('Using response.data structure');
      } else {
        // Si la respuesta ya es los datos directos
        actualData = response;
        console.log('Using direct response structure');
      }
      
      console.log('=== ACTUAL DATA TO USE ===');
      console.log('Actual data:', actualData);
      console.log('Actual data type:', typeof actualData);
      console.log('Actual data keys:', Object.keys(actualData || {}));
      console.log('Columns:', actualData?.columns);
      console.log('Data rows:', actualData?.data);
      console.log('Rows count:', actualData?.data?.length);
      console.log('Execution time:', actualData?.execution_time_ms);
      console.log('=== END QUERY RESPONSE ANALYSIS ===');
      
      setResults(actualData);
      setExecutionTime(actualData?.execution_time_ms || 0);
      
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

    // Verificar si tenemos datos en formato esperado del backend
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
