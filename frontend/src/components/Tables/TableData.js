import React, { useState, useEffect } from 'react';
import { Table, Alert, Pagination, Card, Button } from 'react-bootstrap';
import { useParams, useNavigate } from 'react-router-dom';
import { tableService } from '../../services/api';

const TableData = () => {
  const { tableName } = useParams();
  const navigate = useNavigate();
  
  const [data, setData] = useState({ columns: [], rows: [], total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchTableData(currentPage);
  }, [tableName, currentPage]);

  const fetchTableData = async (page) => {
    try {
      setLoading(true);
      const response = await tableService.getTableData(tableName, page);
      setData(response.data);
    } catch (err) {
      setError('Error loading table data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const renderPagination = () => {
    if (data.total_pages <= 1) return null;

    let items = [];
    for (let number = 1; number <= data.total_pages; number++) {
      items.push(
        <Pagination.Item 
          key={number} 
          active={number === currentPage}
          onClick={() => handlePageChange(number)}
        >
          {number}
        </Pagination.Item>
      );
    }

    return (
      <Pagination className="mt-3 justify-content-center">
        <Pagination.First onClick={() => handlePageChange(1)} disabled={currentPage === 1} />
        <Pagination.Prev onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1} />
        {items}
        <Pagination.Next onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === data.total_pages} />
        <Pagination.Last onClick={() => handlePageChange(data.total_pages)} disabled={currentPage === data.total_pages} />
      </Pagination>
    );
  };

  if (loading && currentPage === 1) {
    return <div className="text-center mt-5">Loading table data...</div>;
  }

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Table: {tableName}</h2>
        <Button variant="secondary" onClick={() => navigate('/tables')}>
          Back to Tables
        </Button>
      </div>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      {data.rows.length === 0 ? (
        <Alert variant="info">This table is empty.</Alert>
      ) : (
        <Card>
          <Card.Body>
            <div className="table-responsive">
              <Table striped bordered hover>
                <thead>
                  <tr>
                    {data.columns.map((column, index) => (
                      <th key={index}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {data.columns.map((column, colIndex) => (
                        <td key={colIndex}>{row[column] !== null ? String(row[column]) : 'NULL'}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
            {renderPagination()}
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default TableData;
