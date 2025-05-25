import React, { useState, useEffect } from 'react';
import { Table, Button, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { tableService } from '../../services/api';

const TableList = () => {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTables = async () => {
    try {
      setLoading(true);
      const response = await tableService.listTables();
      
      // Validar que la respuesta tenga la estructura correcta
      console.log('Response from API:', response); // Debug
      
      const tableData = response.data || response || [];
      if (Array.isArray(tableData)) {
        setTables(tableData);
      } else {
        console.error('Invalid response format:', response);
        setTables([]);
        setError('Invalid data format received from server');
      }
    } catch (err) {
      setError('Error loading tables. Please try again.');
      console.error('Error fetching tables:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTables();
  }, []);

  const handleDelete = async (tableName) => {
    if (window.confirm(`Are you sure you want to delete table ${tableName}? This action cannot be undone.`)) {
      try {
        await tableService.deleteTable(tableName);
        fetchTables();
      } catch (err) {
        setError('Error deleting table. Please try again.');
        console.error(err);
      }
    }
  };

  if (loading) return <div className="text-center mt-5">Loading tables...</div>;

  // Mantén toda la lógica existente, solo cambia el return:

return (
  <div className="container fade-in">
    <div className="smart-header">
      <h1>Smart Stock Tables</h1>
      <p>Manage your database tables</p>
    </div>

    {error && <Alert variant="danger">{error}</Alert>}
    
    <div className="d-flex justify-content-between align-items-center mb-4">
      <h2 style={{color: '#1e3a8a', margin: 0}}>My Tables</h2>
      <Link to="/tables/create" className="btn btn-primary">
        + Create Table
      </Link>
    </div>

    {loading ? (
      <div className="loading-state">
        <div className="loading-spinner"></div>
        <p>Loading your tables...</p>
      </div>
    ) : tables.length === 0 ? (
      <div className="empty-state">
        <div className="empty-state-icon">📊</div>
        <h3>No tables found</h3>
        <p>Create your first table to get started with Smart Stock</p>
        <Link to="/tables/create" className="btn btn-primary">
          Create Your First Table
        </Link>
      </div>
    ) : (
      <div className="card-grid">
        {tables.map((table, index) => (
          <div key={table.name} className="card-item slide-in-left" style={{animationDelay: `${index * 0.1}s`}}>
            <div className="card-title">{table.name}</div>
            <div className="card-subtitle">Database Table</div>
            
            <div style={{margin: '15px 0'}}>
              <div className="d-flex justify-content-between mb-2">
                <span style={{color: '#64748b'}}>Columns:</span>
                <strong>{table.columns?.length || 0}</strong>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span style={{color: '#64748b'}}>Rows:</span>
                <strong>{table.row_count?.toLocaleString() || 0}</strong>
              </div>
              <div className="d-flex justify-content-between">
                <span style={{color: '#64748b'}}>Created:</span>
                <strong>{new Date(table.created_at).toLocaleDateString()}</strong>
              </div>
            </div>
            
            <div className="card-actions">
              <Link to={`/tables/${table.name}`} className="btn btn-secondary btn-sm">
                View Data
              </Link>
              <button 
                onClick={() => handleDelete(table.name)} 
                className="btn btn-danger btn-sm"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);
};

export default TableList;
