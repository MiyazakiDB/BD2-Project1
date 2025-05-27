import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Table, Alert, Pagination, Button, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { tableService } from '../../services/api';
import './Tables.css';

const TableData = () => {
  const { tableName } = useParams();
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);

  const fetchTableData = async (page = 1) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await tableService.getTableData(tableName, page);
      
      console.log('=== FRONTEND DEBUG ===');
      console.log('Raw response:', response);
      console.log('Response data:', response.data);
      console.log('Response columns:', response.columns);
      console.log('Sample row:', response.data && response.data[0]);
      console.log('=== END DEBUG ===');
      
      // Validar que la respuesta tenga la estructura correcta
      if (response && typeof response === 'object') {
        const tableData = response.data || [];
        const tableColumns = response.columns || [];
        
        console.log('Setting data:', tableData);
        console.log('Setting columns:', tableColumns);
        
        setData(tableData);
        setColumns(tableColumns);
        setCurrentPage(response.current_page || 1);
        setTotalPages(response.total_pages || 1);
        setTotalRows(response.total_rows || 0);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Error fetching table data:', err);
      setError(`Error loading table data: ${err.message}`);
      // Asegurar que los estados tengan valores por defecto
      setData([]);
      setColumns([]);
      setCurrentPage(1);
      setTotalPages(1);
      setTotalRows(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tableName) {
      fetchTableData(1);
    }
  }, [tableName]);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    fetchTableData(page);
  };

  if (loading) {
    return (
      <div className="table-data-loading-container">
        <div className="table-data-loading-spinner"></div>
        <p className="table-data-loading-text">Loading table data...</p>
      </div>
    );
  }

  return (
    <div className="table-data-container">
      <div className="table-data-wrapper">
        {/* Header */}
        <div className="table-data-header">
          <Link to="/tables" className="table-data-back-btn">
            ← Back to Tables
          </Link>
          <div className="table-data-title-section">
            <h1 className="table-data-main-title">📊 {tableName}</h1>
            <p className="table-data-subtitle">View and manage table data</p>
          </div>
        </div>

        {/* Controls */}
        <div className="table-data-controls">
          <div className="table-data-info">
            <span className="table-data-info-text">
              Showing {((currentPage - 1) * 50) + 1} to {Math.min(currentPage * 50, totalRows)} of {totalRows} rows
            </span>
          </div>
          <div>
            <Link to="/query" style={{ 
              background: '#0E3459',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '10px',
              textDecoration: 'none',
              fontWeight: '600',
              transition: 'all 0.3s ease'
            }}>
              🔍 Query Table
            </Link>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="table-data-error-alert">
            ❌ {error}
          </div>
        )}

        {!error && (
          <>
            {data && data.length > 0 ? (
              <div className="table-data-content">
                <div className="table-data-scroll-container">
                  <table className="table-data-table">
                    <thead className="table-data-thead">
                      <tr className="table-data-header-row">
                        {columns && columns.length > 0 ? (
                          columns.map((column, index) => (
                            <th key={index} className="table-data-th">{column}</th>
                          ))
                        ) : (
                          <th className="table-data-th">No columns defined</th>
                        )}
                      </tr>
                    </thead>
                    <tbody className="table-data-tbody">
                      {data.map((row, rowIndex) => {
                        console.log(`Rendering row ${rowIndex}:`, row); // Debug
                        return (
                          <tr 
                            key={rowIndex} 
                            className="table-data-row"
                            style={{ animationDelay: `${rowIndex * 0.05}s` }}
                          >
                            {Array.isArray(row) ? (
                              row.map((cell, cellIndex) => {
                                const cellValue = cell !== null && cell !== undefined ? String(cell) : '';
                                console.log(`Cell [${rowIndex}][${cellIndex}]:`, cell, '-> displayed as:', cellValue); // Debug
                                return (
                                  <td key={cellIndex} className="table-data-td">
                                    <div className="table-data-cell-content">
                                      {cellValue || <span className="table-data-null">NULL</span>}
                                    </div>
                                  </td>
                                );
                              })
                            ) : (
                              <td colSpan={columns.length || 1} className="table-data-td">
                                Invalid row data: {typeof row} - {JSON.stringify(row)}
                              </td>
                            )}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="table-data-pagination">
                    <button
                      onClick={() => handlePageChange(1)}
                      disabled={currentPage === 1}
                      className="table-data-pagination-btn table-data-pagination-prev"
                    >
                      ← First
                    </button>
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="table-data-pagination-btn table-data-pagination-prev"
                    >
                      ← Previous
                    </button>

                    <div className="table-data-pagination-pages">
                      {[...Array(Math.min(totalPages, 10))].map((_, index) => {
                        const page = index + 1;
                        return (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className={`table-data-pagination-btn ${currentPage === page ? 'table-data-pagination-active' : ''}`}
                          >
                            {page}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="table-data-pagination-btn table-data-pagination-next"
                    >
                      Next →
                    </button>
                    <button
                      onClick={() => handlePageChange(totalPages)}
                      disabled={currentPage === totalPages}
                      className="table-data-pagination-btn table-data-pagination-next"
                    >
                      Last →
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="table-data-empty-state">
                <div className="table-data-empty-icon">📊</div>
                <h3 className="table-data-empty-title">No data found</h3>
                <p className="table-data-empty-subtitle">This table is empty</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TableData;