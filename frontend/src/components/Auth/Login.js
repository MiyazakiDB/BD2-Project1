import React, { useState } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../../services/api';

const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await authService.login(credentials);
      
      // Debug: ver qué devuelve exactamente el servidor
      console.log('Login response:', response);
      console.log('Response data:', response.data);
      
      // Verificar diferentes formatos de token
      let token = null;
      if (response.data) {
        // Intentar access_token primero, luego token
        token = response.data.access_token || response.data.token;
      }
      
      if (!token) {
        console.error('No token found in response. Response data:', response.data);
        throw new Error('No se recibió un token válido del servidor');
      }
      
      // Almacenar el token
      localStorage.setItem('token', token);
      
      console.log('Token guardado correctamente:', token);
      
      // Llamar a onLogin para actualizar el estado de autenticación
      onLogin();
      
      navigate('/files');
    } catch (err) {
      console.error('Login error:', err);
      console.error('Error response:', err.response);
      
      // Mejorar el manejo de errores para evitar renderizar objetos
      let errorMessage = 'Error iniciando sesión. Verifica tus credenciales.';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // Si es un array de errores de validación
        if (Array.isArray(errorData) && errorData.length > 0) {
          errorMessage = errorData.map(error => {
            if (typeof error === 'string') return error;
            return error.msg || error.message || 'Error de validación';
          }).join(', ');
        }
        // Si es un objeto con detail
        else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(error => {
              if (typeof error === 'string') return error;
              return error.msg || error.message || 'Error de validación';
            }).join(', ');
          } else {
            errorMessage = 'Error de validación del servidor';
          }
        }
        // Si es un objeto con message
        else if (errorData.message && typeof errorData.message === 'string') {
          errorMessage = errorData.message;
        }
        // Si es un string directamente
        else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
        // Para cualquier otro caso, usar mensaje genérico
        else {
          errorMessage = 'Error del servidor';
        }
      }
      // Si es un error de red sin respuesta
      else if (err.message && typeof err.message === 'string') {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="smart-header">
        <h1>Smart Stock</h1>
        <p>Database Management System</p>
      </div>
      
      <div className="auth-form">
        <h2 className="text-center mb-4">Welcome Back</h2>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Username</Form.Label>
            <Form.Control
              type="text"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
              placeholder="Enter your username"
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </Form.Group>

          <Button variant="primary" type="submit" disabled={loading} className="w-100">
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
          
          <div className="text-center mt-3">
            Don't have an account? <Link to="/register" style={{color: '#2563eb', fontWeight: '500'}}>Create Account</Link>
          </div>
        </Form>
      </div>
    </div>
  );
};

export default Login;