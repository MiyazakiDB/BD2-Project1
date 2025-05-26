import React, { useState } from 'react';
import { Form, Button, Alert, Card, Row, Col, Badge } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { tableService } from '../../services/api';
import './Tables.css';

const CreateTable = () => {
  const navigate = useNavigate();
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState([{ name: '', data_type: 'INT', is_indexed: false }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [hasHeaders, setHasHeaders] = useState(true);

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
    formData.append('has_headers', hasHeaders.toString());
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
    <div className="create-table-container">
      <div className="create-table-wrapper">
        {/* Header */}
        <div className="create-table-header">
          <Link to="/tables" className="create-table-back-btn">
            ← Back
          </Link>
          <div className="create-table-title-section">
            <h1 className="create-table-main-title">➕ Create New Table</h1>
            <p className="create-table-subtitle">Define your table structure and upload data</p>
          </div>
        </div>

        {/* Main Create Card */}
        <div className="create-table-card">
          {/* Alerts */}
          {error && (
            <div className="create-table-error-alert">
              ❌ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="create-table-form">
            {/* Table Name Section */}
            <div className="create-table-section">
              <label className="create-table-label">Table Name</label>
              <input
                type="text"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="create-table-input"
                placeholder="Enter table name (e.g., products, customers)"
                required
              />
            </div>

            {/* File Section */}
            <div className="create-table-section">
              <label className="create-table-label">Data File</label>
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                className="create-table-input"
                accept=".csv,.xlsx,.xls"
                required
              />
              <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0.5rem 0 0 0' }}>
                Upload CSV, XLSX, or XLS files with your data
              </p>
            </div>

            {/* Headers Section */}
            <div className="create-table-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <label className="create-table-label" style={{ marginBottom: 0 }}>File Header Settings</label>
                <span className={`badge ${hasHeaders ? 'bg-success' : 'bg-secondary'}`} style={{ 
                  background: hasHeaders ? '#16a34a' : '#64748b',
                  color: 'white',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '0.8rem'
                }}>
                  {hasHeaders ? 'Headers: YES' : 'Headers: NO'}
                </span>
              </div>
              <label className="create-table-checkbox-label">
                <input
                  type="checkbox"
                  checked={hasHeaders}
                  onChange={(e) => setHasHeaders(e.target.checked)}
                  className="create-table-checkbox"
                />
                <span className="create-table-checkbox-text">File has headers (first line contains column names)</span>
              </label>
            </div>

            {/* Columns Section */}
            <div className="create-table-section">
              <div className="create-table-columns-header">
                <label className="create-table-label">Column Definitions</label>
                <button
                  type="button"
                  onClick={addColumn}
                  className="create-table-add-column-btn"
                >
                  ➕ Add Column
                </button>
              </div>

              <div className="create-table-columns-list">
                {columns.map((column, index) => (
                  <div key={index} className="create-table-column-row">
                    <div className="create-table-column-inputs">
                      <input
                        type="text"
                        value={column.name}
                        onChange={(e) => handleColumnChange(index, 'name', e.target.value)}
                        className="create-table-column-input"
                        placeholder="Column name..."
                        required
                      />
                      
                      <select
                        value={column.data_type}
                        onChange={(e) => handleColumnChange(index, 'data_type', e.target.value)}
                        className="create-table-column-select"
                        required
                      >
                        {dataTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>

                      <label className="create-table-checkbox-label">
                        <input
                          type="checkbox"
                          checked={column.is_indexed}
                          onChange={(e) => handleColumnChange(index, 'is_indexed', e.target.checked)}
                          className="create-table-checkbox"
                        />
                        <span className="create-table-checkbox-text">Create Index</span>
                      </label>
                    </div>

                    {columns.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeColumn(index)}
                        className="create-table-remove-column-btn"
                      >
                        ❌
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="create-table-actions">
              <Link to="/tables" className="create-table-cancel-btn">
                ← Back to Tables
              </Link>

              <button
                type="submit"
                disabled={loading}
                className={`create-table-submit-btn ${loading ? 'create-table-submit-disabled' : ''}`}
              >
                {loading ? (
                  <>
                    <div className="create-table-spinner"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    🏗️ Create Table
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateTable;