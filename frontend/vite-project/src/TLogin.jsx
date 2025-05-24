import React, { useState } from 'react';
import './Auth.css';
import WaveSketch from './WaveSketch';
import logo from './assets/logo.svg';

export default function TLogin() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login data:', formData);
   

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
          <a href="/" className="auth-nav-link login-active">Login</a>
          <a href="/register" className="auth-nav-link">Register</a>
        </div>
      </div>

      <div className="auth-content">
        <div className="auth-card">
          <h1 className="auth-title">Welcome!</h1>
          
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
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
                value={formData.password}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>

            <button type="submit" className="auth-button">
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}