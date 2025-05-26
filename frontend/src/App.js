import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Sidebar from './components/Layout/Sidebar';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import FileList from './components/Files/FileList';
import FileUpload from './components/Files/FileUpload';
import TableList from './components/Tables/TableList';
import CreateTable from './components/Tables/CreateTable';
import TableData from './components/Tables/TableData';
import QueryExecutor from './components/Query/QueryExecutor';
import MetricsDisplay from './components/Metrics/MetricsDisplay';
import Landing from './components/Landing/Landing';
import { Container, Row, Col } from 'react-bootstrap';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token');
      setIsAuthenticated(!!token);
    };
    checkAuth();
    window.addEventListener('storage', checkAuth);
    return () => {
      window.removeEventListener('storage', checkAuth);
    };
  }, []);

  const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('token');
    if (!token) {
      return <Navigate to="/login" />;
    }
    return children;
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    navigate('/login');
  };

  return (
    <div className="App">
     
      <Container fluid>
        {isAuthenticated ? (
          <Row>
            <Col md={3} lg={2} className="sidebar">
              <Sidebar />
            </Col>
            <Col md={9} lg={10} className="content-area">
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/files" element={<ProtectedRoute><FileList /></ProtectedRoute>} />
                <Route path="/files/upload" element={<ProtectedRoute><FileUpload /></ProtectedRoute>} />
                <Route path="/tables" element={<ProtectedRoute><TableList /></ProtectedRoute>} />
                <Route path="/tables/create" element={<ProtectedRoute><CreateTable /></ProtectedRoute>} />
                <Route path="/tables/:tableName" element={<ProtectedRoute><TableData /></ProtectedRoute>} />
                <Route path="/query" element={<ProtectedRoute><QueryExecutor /></ProtectedRoute>} />
                <Route path="/metrics" element={<ProtectedRoute><MetricsDisplay /></ProtectedRoute>} />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </Col>
          </Row>
        ) : (
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="/register" element={<Register onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        )}
      </Container>
    </div>
  );
}

export default App;