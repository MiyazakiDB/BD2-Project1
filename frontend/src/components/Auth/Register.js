import React, { useState } from 'react';
import './Auth.css';
import WaveSketch from './WaveSketch';
import logo from '../../assets/logo.svg';
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
        localStorage.setItem('token', response.data.token);
        onLogin();
        navigate('/files');
      } else if (response.data && response.data.message) {
        // Intentar iniciar sesión automáticamente con las credenciales
        try {
          const loginResponse = await authService.login({
            username: userData.username,
            password: userData.password
          });
          if (loginResponse.data && loginResponse.data.token) {
            localStorage.setItem('token', loginResponse.data.token);
            onLogin();
            navigate('/files');
          } else {
            setError('Registro exitoso. Por favor inicia sesión.');
            navigate('/login');
          }
        } catch (loginErr) {
          setError('Registro exitoso. Por favor inicia sesión manualmente.');
          navigate('/login');
        }
      } else {
        setError('Registro completado con formato de respuesta inesperado. Intenta iniciar sesión.');
        navigate('/login');
      }
    } catch (err) {
      let errorMessage = 'Error durante el registro. Por favor intenta nuevamente.';
      if (err.response?.data) {
        const errorData = err.response.data;
        if (Array.isArray(errorData) && errorData.length > 0) {
          errorMessage = errorData.map(error => error.msg || error.message || String(error)).join(', ');
        } else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(error => error.msg || error.message || String(error)).join(', ');
          } else {
            errorMessage = String(errorData.detail);
          }
        } else if (errorData.message) {
          errorMessage = String(errorData.message);
        } else if (err.response.status === 400) {
          errorMessage = 'Datos de registro inválidos. Verifica los campos.';
        } else if (err.response.status === 409) {
          errorMessage = 'El nombre de usuario o email ya está en uso.';
        } else if (typeof errorData === 'object') {
          errorMessage = 'Error en los datos de registro.';
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <WaveSketch />

      <div className="auth-navbar">
        <div
          className="auth-logo"
          style={{ cursor: 'pointer' }}
          onClick={() => window.location.href = '/'}
        >
          <img src={logo} alt="Smart Stock Logo" />
        </div>
        <div className="auth-nav-links">
          <Link to="/login" className="auth-nav-link">Login</Link>
          <Link to="/register" className="auth-nav-link register-active">Register</Link>
        </div>
      </div>

      <div className="auth-content">
        <div className="auth-card register-card">
          <div className="register-layout">
            <div className="register-left">
              <h2 className="register-slogan">
                It's Time<br />
                to Take<br />
                Charge of<br />
                Your<br />
                Stock
              </h2>
            </div>

            <div className="register-divider"></div>

            <div className="register-right">
              <h1 className="auth-title">Create An Account</h1>
              {error && (
                <div className="mb-3" style={{
                  background: 'rgba(255,0,0,0.08)',
                  color: '#b91c1c',
                  borderRadius: '12px',
                  padding: '12px 18px',
                  marginBottom: '1.5rem',
                  border: '1px solid #fca5a5'
                }}>
                  {error}
                </div>
              )}
              <form onSubmit={handleSubmit} className="auth-form">
                <div className="form-group">
                  <label htmlFor="username" className="form-label">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={userData.username}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email" className="form-label">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={userData.email}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="password" className="form-label">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={userData.password}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>

                <button type="submit" className="auth-button" disabled={loading}>
                  {loading ? 'Creating account...' : 'Register'}
                </button>
              </form>
              <div style={{ textAlign: 'center', marginTop: '1.5rem', color: '#fff' }}>
                Already have an account?{' '}
                <Link to="/login" style={{ color: '#FFD700', fontWeight: 'bold', textDecoration: 'underline' }}>
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;