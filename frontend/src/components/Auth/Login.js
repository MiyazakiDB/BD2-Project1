import React, { useState } from 'react';
import './Auth.css';
import WaveSketch from './WaveSketch';
import logo from '../../assets/logo.svg';
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
      let token = null;
      if (response.data) {
        token = response.data.access_token || response.data.token;
      }
      if (!token) {
        throw new Error('No se recibió un token válido del servidor');
      }
      localStorage.setItem('token', token);
      onLogin();
      navigate('/files');
    } catch (err) {
      let errorMessage = 'Error iniciando sesión. Verifica tus credenciales.';
      if (err.response?.data) {
        const errorData = err.response.data;
        if (Array.isArray(errorData) && errorData.length > 0) {
          errorMessage = errorData.map(error => {
            if (typeof error === 'string') return error;
            return error.msg || error.message || 'Error de validación';
          }).join(', ');
        } else if (errorData.detail) {
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
        } else if (errorData.message && typeof errorData.message === 'string') {
          errorMessage = errorData.message;
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else {
          errorMessage = 'Error del servidor';
        }
      } else if (err.message && typeof err.message === 'string') {
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
          <Link to="/login" className="auth-nav-link login-active">Login</Link>
          <Link to="/register" className="auth-nav-link">Register</Link>
        </div>
      </div>

      <div className="auth-content">
        <div className="auth-card">
          <h1 className="auth-title">Welcome!</h1>
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
                value={credentials.username}
                onChange={handleChange}
                className="form-input"
                required
                autoComplete="username"
                placeholder="Enter your username"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={credentials.password}
                onChange={handleChange}
                className="form-input"
                required
                autoComplete="current-password"
                placeholder="Enter your password"
              />
            </div>

            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '1.5rem', color: '#fff' }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#FFD700', fontWeight: 'bold', textDecoration: 'underline' }}>
              Create Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;