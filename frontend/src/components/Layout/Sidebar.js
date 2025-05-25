import React from 'react';
import { Nav } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const location = useLocation();
  
  return (
    <Nav className="flex-column pt-3">
      <Nav.Item>
        <Nav.Link as={Link} to="/files" active={location.pathname === '/files'}>
          Files
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/files/upload" active={location.pathname === '/files/upload'}>
          Upload File
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/tables" active={location.pathname === '/tables'}>
          Tables
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/tables/create" active={location.pathname === '/tables/create'}>
          Create Table
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/query" active={location.pathname === '/query'}>
          Query Executor
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/metrics" active={location.pathname === '/metrics'}>
          Metrics
        </Nav.Link>
      </Nav.Item>
    </Nav>
  );
};

export default Sidebar;
