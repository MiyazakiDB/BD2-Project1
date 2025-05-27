import React, { useState } from 'react';
import { Form, Button, Alert, Table, Card } from 'react-bootstrap';
import { queryService } from '../../services/api';
import './Query.css';

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
      console.log('Query to execute:', query); // Verifica que la consulta sea correcta

      const response = await queryService.executeQuery(query);

      console.log('=== RAW RESPONSE FROM API SERVICE ===');
      console.log('Full response:', response);
      setResults(response);
      setExecutionTime(response?.execution_time_ms || 0);
    } catch (err) {
      console.error('=== QUERY EXECUTION ERROR ===');
      console.error('Error object:', err);
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
        <div className="query-results-container">
          <div className="query-results-header">
            <h4 className="query-results-title">📊 Query Results</h4>
            <div className="query-results-stats">
              <span className="query-stat-badge">
                📄 {results.data.length} rows
              </span>
              <span className="query-stat-badge">
                ⚡ {results.execution_time_ms?.toFixed(2) || 0} ms
              </span>
            </div>
          </div>
          
          <div className="query-table-container">
            <div className="query-table-scroll">
              <table className="query-table">
                <thead className="query-table-header">
                  <tr>
                    {results.columns && results.columns.map((col, index) => (
                      <th key={index} className="query-table-th">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="query-table-body">
                  {results.data.map((row, rowIndex) => (
                    <tr key={rowIndex} className="query-table-row" style={{ animationDelay: `${rowIndex * 0.05}s` }}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex} className="query-table-td">
                          <div className="query-cell-content">
                            {cell !== null ? String(cell) : <span className="query-null">NULL</span>}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="query-results-footer">
            <span className="query-footer-text">
              Rows affected: {results.rows_affected || results.data.length} | 
              Execution time: {results.execution_time_ms?.toFixed(2) || 0} ms
            </span>
          </div>
        </div>
      );
    }
    
    // Verificar formato legacy (si existiera)
    else if (results.rows && results.rows.length > 0) {
      console.log('Rendering table with legacy format');
      return (
        <div className="query-results-container">
          <div className="query-results-header">
            <h4 className="query-results-title">📊 Query Results</h4>
            <span className="query-stat-badge">📄 {results.rows.length} rows</span>
          </div>
          
          <div className="query-table-container">
            <div className="query-table-scroll">
              <table className="query-table">
                <thead className="query-table-header">
                  <tr>
                    {Object.keys(results.rows[0]).map(key => (
                      <th key={key} className="query-table-th">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="query-table-body">
                  {results.rows.map((row, index) => (
                    <tr key={index} className="query-table-row">
                      {Object.values(row).map((value, i) => (
                        <td key={i} className="query-table-td">
                          <div className="query-cell-content">
                            {value !== null ? String(value) : <span className="query-null">NULL</span>}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    }
    
    // Verificar si hay mensaje de operación
    else if (results.message) {
      console.log('Rendering message:', results.message);
      return (
        <div className="query-success-alert">
          ✅ {results.message}
        </div>
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
        <div className="query-info-alert">
          Query executed successfully. No results to display.
          <details className="query-debug-details">
            <summary>Debug Info</summary>
            <pre className="query-debug-content">{JSON.stringify(results, null, 2)}</pre>
          </details>
        </div>
      );
    }
  };

  return (
    <div className="query-container">
      <div className="query-wrapper">
        {/* Header */}
        <div className="query-header">
          <div className="query-title-section">
            <h1 className="query-main-title">🔍 SQL Query Executor</h1>
            <p className="query-subtitle">Execute custom SQL queries on your database</p>
          </div>
        </div>

        {/* Main Query Card */}
        <div className="query-card">
          <div className="query-card-header">
            <div className="query-card-icon">⚡</div>
            <h3 className="query-card-title">Query Console</h3>
          </div>

          <form onSubmit={handleSubmit} className="query-form">
            {/* Query Input Section */}
            <div className="query-section">
              <label className="query-label">SQL Query</label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="query-textarea"
                rows={8}
                placeholder="-- Enter your SQL query here
SELECT * FROM table_name;
-- Examples:
-- SELECT COUNT(*) FROM products;
-- UPDATE users SET status = 'active' WHERE id = 1;
-- INSERT INTO categories (name) VALUES ('Electronics');"
              />
              <div className="query-input-footer">
                <span className="query-input-hint">💡 Tip: Use standard SQL syntax. Be careful with UPDATE/DELETE operations.</span>
              </div>
            </div>

            {/* Action Button */}
            <div className="query-actions">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className={`query-submit-btn ${loading || !query.trim() ? 'query-submit-disabled' : ''}`}
              >
                {loading ? (
                  <>
                    <div className="query-spinner"></div>
                    Executing Query...
                  </>
                ) : (
                  <>
                    ⚡ Execute Query
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="query-error-alert">
            ❌ {error}
          </div>
        )}
        
        {/* Execution Time Alert */}
        {executionTime !== null && !error && (
          <div className="query-execution-alert">
            ⚡ Query executed successfully in {executionTime.toFixed(2)} ms
          </div>
        )}

        {/* Results */}
        {renderResults()}
      </div>
    </div>
  );
};

export default QueryExecutor;