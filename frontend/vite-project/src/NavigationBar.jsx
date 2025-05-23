import React, { useState } from 'react';
import boxLogo from './assets/box-logo.svg';
import './NavigationBar.css';

export default function NavigationBar() {
  const [visible, setVisible] = useState(true);

  const handleNavClick = () => setVisible(false);

  if (!visible) return null;

  return (
    <nav className="navbar-bar">
      <div className="navbar-logo">
        <img src={boxLogo} alt="Smart Stock" />
        <div className="navbar-title">SMART STOCK</div>
      </div>
      <ul className="navbar-links">
        <li><button onClick={handleNavClick}>Dashboard</button></li>
        <li><button onClick={handleNavClick}>Query console</button></li>
        <li><button onClick={handleNavClick}>Configuration</button></li>
      </ul>
      <div className="navbar-account">
        Account : nickname-user.gmail
      </div>
    </nav>
  );
}