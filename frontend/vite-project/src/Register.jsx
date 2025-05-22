import React, { useState } from 'react';
import './Auth.css';
import WaveSketch from './WaveSketch';
import logo from './assets/logo.svg';

export default function Register() {
  const [formData, setFormData] = useState({
    name: '',
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
    console.log('Register data:', formData);



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
          <a href="/login" className="auth-nav-link">Login</a>
          <a href="/register" className="auth-nav-link register-active">Register</a>
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
              
              <form onSubmit={handleSubmit} className="auth-form">
                <div className="form-group">
                  <label htmlFor="name" className="form-label">Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
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
                  Register
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}