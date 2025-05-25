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
      setTables(response.data);
    } catch (err) {
      setError('Error loading tables. Please try again.');
      console.error(err);
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

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>My Tables</h2>
        <Button as={Link} to="/tables/create" variant="primary">
          Create New Table
        </Button>
      </div>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      {tables.length === 0 ? (
        <Alert variant="info">You don't have any tables yet. Create your first table!</Alert>
      ) : (
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Table Name</th>
              <th>Columns</th>
              <th>Created Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tables.map((table) => (
              <tr key={table.name}>
                <td>{table.name}</td>
                <td>{table.columns.length}</td>
                <td>{new Date(table.created_at).toLocaleString()}</td>
                <td>
                  <Button 
                    variant="primary" 
                    size="sm"
                    as={Link}
                    to={`/tables/${table.name}`}
                    className="me-2"
                  >
                    View Data
                  </Button>
                  <Button 
                    variant="danger" 
                    size="sm"
                    onClick={() => handleDelete(table.name)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
};

export default TableList;
