import React, { useState, useEffect } from 'react';
import { Table, Button, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { tableService } from '../../services/api';
import './Tables.css';

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

  if (loading) return <div className="tables-loading-container">
    <div className="tables-loading-spinner"></div>
    <p className="tables-loading-text">Loading tables...</p>
  </div>;

  return (
    <div className="tables-container">
      <div className="tables-wrapper">
        {/* Header */}
        <div className="tables-header">
          <div className="tables-header-content">
            <div className="tables-title-section">
              <h1 className="tables-main-title">🗃️ Database Tables</h1>
              <p className="tables-subtitle">Manage your database tables and structures</p>
            </div>
            <Link to="/tables/create" className="tables-create-btn">
              ➕ Create New Table
            </Link>
          </div>

          {/* Stats Cards */}
          <div className="tables-stats-grid">
            <div className="tables-stat-card">
              <div className="tables-stat-icon">📊</div>
              <div className="tables-stat-info">
                <p className="tables-stat-label">Total Tables</p>
                <p className="tables-stat-value">{tables.length}</p>
              </div>
            </div>
            
            <div className="tables-stat-card">
              <div className="tables-stat-icon">🔗</div>
              <div className="tables-stat-info">
                <p className="tables-stat-label">Active Connections</p>
                <p className="tables-stat-value">1</p>
              </div>
            </div>

            <div className="tables-stat-card">
              <div className="tables-stat-icon">⚡</div>
              <div className="tables-stat-info">
                <p className="tables-stat-label">Status</p>
                <p className="tables-stat-value">Online</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="tables-error-alert">
            ❌ {error}
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="tables-loading-container">
            <div className="tables-loading-spinner"></div>
            <p className="tables-loading-text">Loading your tables...</p>
          </div>
        ) : tables.length === 0 ? (
          /* Empty State */
          <div className="tables-empty-state">
            <div className="tables-empty-icon">🗃️</div>
            <h3 className="tables-empty-title">No tables found</h3>
            <p className="tables-empty-subtitle">Create your first database table to get started</p>
            <Link to="/tables/create" className="tables-empty-create-btn">
              ➕ Create Your First Table
            </Link>
          </div>
        ) : (
          /* Tables Grid */
          <div className="tables-grid">
            {tables.map((table, index) => (
              <div
                key={table.name}
                className="tables-card"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="tables-card-header">
                  <div className="tables-card-icon">🗃️</div>
                  <button
                    onClick={() => handleDelete(table.name)}
                    className="tables-delete-btn"
                  >
                    🗑️
                  </button>
                </div>
                
                <h3 className="tables-card-title">{table.name}</h3>
                
                <div className="tables-card-details">
                  <div className="tables-card-detail">
                    <span>Columns:</span>
                    <span>{table.columns?.length || 0}</span>
                  </div>
                  <div className="tables-card-detail">
                    <span>Rows:</span>
                    <span>{table.row_count?.toLocaleString() || 0}</span>
                  </div>
                  <div className="tables-card-detail">
                    <span>Created:</span>
                    <span>{new Date(table.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="tables-card-actions">
                  <Link to={`/tables/${table.name}`} className="tables-view-btn">
                    👁️ View Data
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TableList;