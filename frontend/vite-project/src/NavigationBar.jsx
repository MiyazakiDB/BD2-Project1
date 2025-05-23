import React, { useState } from 'react';
import { Menu, X, Home, Search, Settings, User } from 'lucide-react';
import logo from './assets/logo.svg';
import './NavigationBar.css';

export default function NavigationBar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeItem, setActiveItem] = useState('Dashboard');

  const navItems = [
    { name: 'Dashboard', icon: Home },
    { name: 'Query console', icon: Search },
    { name: 'Configuration', icon: Settings }
  ];

  const handleNavClick = (itemName) => {
    setActiveItem(itemName);
    // Here you would typically handle navigation/routing
    console.log(`Navigating to: ${itemName}`);
  };

  const toggleNavbar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <>
      {/* Toggle button for mobile/collapsed state */}
      {isCollapsed && (
        <button 
          onClick={toggleNavbar}
          className="navbar-toggle-btn"
        >
          <Menu size={20} />
        </button>
      )}

      <nav className={`navbar-bar ${isCollapsed ? 'navbar-collapsed' : ''}`}>
        
        {/* Header with logo and collapse button */}
        <div>
          <div className="navbar-header">
            <div className="navbar-logo">
              <img src={logo} alt="Smart Stock" className="navbar-logo-img" />
              <div className="navbar-title">SMART STOCK</div>
            </div>
            <button
              onClick={toggleNavbar}
              className="navbar-close-btn"
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation Links */}
          <ul className="navbar-links">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = activeItem === item.name;
              
              return (
                <li key={item.name}>
                  <button
                    onClick={() => handleNavClick(item.name)}
                    className={`navbar-link-btn ${isActive ? 'active' : ''}`}
                  >
                    <IconComponent size={18} />
                    <span>{item.name}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Account section */}
        <div className="navbar-account">
          <div className="navbar-account-info">
            <div className="navbar-account-avatar">
              <User size={16} />
            </div>
            <div className="navbar-account-details">
              <div className="navbar-account-label">Account</div>
              <div className="navbar-account-email">nickname-user@gmail.com</div>
            </div>
          </div>
        </div>
      </nav>

      {/* Overlay for mobile */}
      {!isCollapsed && (
        <div className="navbar-overlay" onClick={toggleNavbar}></div>
      )}
    </>
  );
}