import React, { useState, useEffect } from 'react'
import { Cloud, ChevronRight, Bell, Settings, LogOut, Moon, Sun } from 'lucide-react'
import { api } from '../api'

// Sidebar Navigation
export function Sidebar({ navItems, activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo"><Cloud size={20} /></div>
        <div>
          <div className="sidebar-title">MiniCloud</div>
          <div className="sidebar-subtitle">Control Plane</div>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map(section => (
          <div key={section.section} className="nav-section">
            <div className="nav-section-title">{section.section}</div>
            {section.items.map(item => (
              <div
                key={item.id}
                className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => setActivePage(item.id)}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
                {item.badge && <span className="nav-item-badge">{item.badge}</span>}
              </div>
            ))}
          </div>
        ))}
      </nav>
      
      <div className="sidebar-footer">
        <div className="sidebar-version">v1.0.0</div>
      </div>
    </aside>
  )
}

// Header with API status, search, and user menu
export function Header({ title, subtitle }) {
  const [health, setHealth] = useState(null)
  const [showUserMenu, setShowUserMenu] = useState(false)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await api.health()
        setHealth(result)
      } catch {
        setHealth({ status: 'error' })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="header">
      <div className="header-left">
        <div className="breadcrumb">
          <span>MiniCloud</span>
          <ChevronRight size={14} className="breadcrumb-separator" />
          <span className="breadcrumb-current">{title}</span>
        </div>
        {subtitle && <div className="header-subtitle">{subtitle}</div>}
      </div>
      
      <div className="header-right">
        <div className={`api-status ${health?.status === 'healthy' ? 'online' : 'offline'}`}>
          <span className="status-dot" />
          API {health?.status === 'healthy' ? 'Online' : 'Offline'}
        </div>
        
        <button className="header-icon-btn" title="Notifications">
          <Bell size={18} />
        </button>
        
        <button className="header-icon-btn" title="Settings">
          <Settings size={18} />
        </button>
        
        <div className="header-user" onClick={() => setShowUserMenu(!showUserMenu)}>
          <div className="header-user-avatar">A</div>
          <div className="header-user-info">
            <div className="header-user-name">Admin</div>
            <div className="header-user-role">Organization Owner</div>
          </div>
          
          {showUserMenu && (
            <div className="user-menu">
              <div className="user-menu-item">
                <Settings size={16} /> Settings
              </div>
              <div className="user-menu-item">
                <LogOut size={16} /> Sign Out
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

// Page Layout wrapper
export function PageLayout({ title, subtitle, actions, children }) {
  return (
    <div className="page fade-in">
      <div className="page-header">
        <div className="page-header-content">
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-description">{subtitle}</p>}
        </div>
        {actions && <div className="page-actions">{actions}</div>}
      </div>
      <div className="page-content">{children}</div>
    </div>
  )
}

// Search Input
export function SearchInput({ value, onChange, placeholder = 'Search...' }) {
  return (
    <div className="search-input-wrapper">
      <input
        type="text"
        className="search-input"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  )
}

// Notification Toast Container
export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div key={toast.id} className={`toast toast-${toast.type}`}>
          <div className="toast-message">{toast.message}</div>
          <button className="toast-close" onClick={() => removeToast(toast.id)}>×</button>
        </div>
      ))}
    </div>
  )
}
