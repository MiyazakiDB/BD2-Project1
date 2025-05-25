import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Table, Alert, Pagination, Button, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { tableService } from '../../services/api';

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
      <div className="text-center mt-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p className="mt-2">Loading table data...</p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Table: {tableName}</h2>
        <div>
          <Button as={Link} to="/tables" variant="secondary" className="me-2">
            Back to Tables
          </Button>
          <Button as={Link} to="/query" variant="primary">
            Query Table
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {!error && (
        <>
          <div className="mb-3">
            <p className="text-muted">
              Showing {((currentPage - 1) * 50) + 1} to {Math.min(currentPage * 50, totalRows)} of {totalRows} rows
            </p>
          </div>

          {data && data.length > 0 ? (
            <>
              <Table striped bordered hover responsive>
                <thead className="table-dark">
                  <tr>
                    {columns && columns.length > 0 ? (
                      columns.map((column, index) => (
                        <th key={index}>{column}</th>
                      ))
                    ) : (
                      <th>No columns defined</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, rowIndex) => {
                    console.log(`Rendering row ${rowIndex}:`, row); // Debug
                    return (
                      <tr key={rowIndex}>
                        {Array.isArray(row) ? (
                          row.map((cell, cellIndex) => {
                            const cellValue = cell !== null && cell !== undefined ? String(cell) : '';
                            console.log(`Cell [${rowIndex}][${cellIndex}]:`, cell, '-> displayed as:', cellValue); // Debug
                            return (
                              <td key={cellIndex}>
                                {cellValue}
                              </td>
                            );
                          })
                        ) : (
                          <td colSpan={columns.length || 1}>
                            Invalid row data: {typeof row} - {JSON.stringify(row)}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </Table>

              {totalPages > 1 && (
                <div className="d-flex justify-content-center mt-4">
                  <Pagination>
                    <Pagination.First 
                      onClick={() => handlePageChange(1)}
                      disabled={currentPage === 1}
                    />
                    <Pagination.Prev 
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    />
                    
                    {[...Array(Math.min(totalPages, 10))].map((_, index) => {
                      const page = index + 1;
                      return (
                        <Pagination.Item
                          key={page}
                          active={page === currentPage}
                          onClick={() => handlePageChange(page)}
                        >
                          {page}
                        </Pagination.Item>
                      );
                    })}
                    
                    <Pagination.Next 
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    />
                    <Pagination.Last 
                      onClick={() => handlePageChange(totalPages)}
                      disabled={currentPage === totalPages}
                    />
                  </Pagination>
                </div>
              )}
            </>
          ) : (
            <Alert variant="info">No data found in this table.</Alert>
          )}
        </>
      )}
    </div>
  );
};

export default TableData;
