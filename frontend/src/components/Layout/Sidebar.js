import React from 'react';
import { Nav, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

const Sidebar = ({ onLogout }) => {
  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <div className="sidebar">
      <div style={{padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)'}}>
        <h4 style={{color: 'white', margin: 0, display: 'flex', alignItems: 'center', gap: '10px'}}>
          <span>💼</span>
          Smart Stock
        </h4>
        <p style={{color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', margin: '5px 0 0 0'}}>
          Database Management
        </p>
      </div>
      
      <Nav className="flex-column" style={{padding: '20px 0'}}>
        <Nav.Link as={Link} to="/files" className="nav-link">
          <span style={{marginRight: '10px'}}>📁</span>
          Files
        </Nav.Link>
        <Nav.Link as={Link} to="/tables" className="nav-link">
          <span style={{marginRight: '10px'}}>📊</span>
          Tables
        </Nav.Link>
        <Nav.Link as={Link} to="/query" className="nav-link">
          <span style={{marginRight: '10px'}}>🔍</span>
          Query Executor
        </Nav.Link>
        <Nav.Link as={Link} to="/metrics" className="nav-link">
          <span style={{marginRight: '10px'}}>📈</span>
          Metrics
        </Nav.Link>
      </Nav>
      
     
    </div>
  );
};

export default Sidebar;