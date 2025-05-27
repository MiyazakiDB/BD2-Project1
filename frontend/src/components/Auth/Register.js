import React, { useState } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../../services/api';

const Register = ({ onLogin }) => {
  const [userData, setUserData] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({ ...userData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await authService.register(userData);
      
      // Si el registro es exitoso, también inicia sesión automáticamente
      if (response.data && response.data.token) {
        // Caso normal: el servidor devuelve un token
        localStorage.setItem('token', response.data.token);
        console.log('Registro exitoso, token guardado');
        onLogin();
        navigate('/files');
      } else if (response.data && response.data.message) {
        // Caso en que el servidor devuelve un mensaje de éxito pero no token
        console.log('Registro exitoso, pero sin token: ', response.data.message);
        
        // Intentar iniciar sesión automáticamente con las credenciales
        try {
          const loginResponse = await authService.login({
            username: userData.username,
            password: userData.password
          });
          
          if (loginResponse.data && loginResponse.data.token) {
            localStorage.setItem('token', loginResponse.data.token);
            console.log('Inicio de sesión automático exitoso después del registro');
            onLogin();
            navigate('/files');
          } else {
            // Registro exitoso pero login fallido
            console.log('No se pudo iniciar sesión automáticamente');
            setError('Registro exitoso. Por favor inicia sesión.');
            navigate('/login');
          }
        } catch (loginErr) {
          console.error('Error en inicio de sesión automático:', loginErr);
          setError('Registro exitoso. Por favor inicia sesión manualmente.');
          navigate('/login');
        }
      } else {
        // Respuesta inesperada
        console.warn('Respuesta inesperada del servidor:', response);
        setError('Registro completado con formato de respuesta inesperado. Intenta iniciar sesión.');
        navigate('/login');
      }
    } catch (err) {
      console.error('Register error:', err);
      
      // Mejorar el manejo de errores para objetos de validación
      let errorMessage = 'Error durante el registro. Por favor intenta nuevamente.';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // Si es un array de errores de validación
        if (Array.isArray(errorData) && errorData.length > 0) {
          errorMessage = errorData.map(error => error.msg || error.message || String(error)).join(', ');
        }
        // Si es un objeto con detail
        else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(error => error.msg || error.message || String(error)).join(', ');
          } else {
            errorMessage = String(errorData.detail);
          }
        }
        // Si es un objeto con message
        else if (errorData.message) {
          errorMessage = String(errorData.message);
        }
        // Manejar errores específicos del backend por código de estado
        else if (err.response.status === 400) {
          errorMessage = 'Datos de registro inválidos. Verifica los campos.';
        } else if (err.response.status === 409) {
          errorMessage = 'El nombre de usuario o email ya está en uso.';
        }
        // Si es cualquier otro tipo de objeto
        else if (typeof errorData === 'object') {
          errorMessage = 'Error en los datos de registro.';
        }
        // Si es un string directamente
        else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
      }
      // Si es un error de red sin respuesta
      else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <h2 className="text-center mb-4">Register</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Username</Form.Label>
          <Form.Control
            type="text"
            name="username"
            value={userData.username}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Email</Form.Label>
          <Form.Control
            type="email"
            name="email"
            value={userData.email}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Password</Form.Label>
          <Form.Control
            type="password"
            name="password"
            value={userData.password}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Button variant="primary" type="submit" disabled={loading} className="w-100">
          {loading ? 'Processing...' : 'Register'}
        </Button>
        
        <div className="text-center mt-3">
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </Form>
    </div>
  );
};

export default Register;
