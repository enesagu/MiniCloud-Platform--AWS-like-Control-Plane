import React from 'react'
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'

// Button Component
export function Button({ children, variant = 'primary', size = 'md', icon: Icon, loading, disabled, ...props }) {
  const classes = `btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''} ${loading ? 'loading' : ''}`
  return (
    <button className={classes} disabled={disabled || loading} {...props}>
      {loading ? <span className="spinner" /> : Icon && <Icon size={size === 'sm' ? 12 : 16} />}
      {children}
    </button>
  )
}

// Card Component
export function Card({ title, icon: Icon, action, children, className = '' }) {
  return (
    <div className={`card ${className}`}>
      {(title || action) && (
        <div className="card-header">
          {title && <div className="card-title">{Icon && <Icon size={16} />}{title}</div>}
          {action}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  )
}

// Modal Component
export function Modal({ open, onClose, title, children, footer, size = 'md' }) {
  if (!open) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className={`modal modal-${size}`} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">{title}</div>
          <button className="btn btn-sm btn-secondary" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

// Status Badge
export function Status({ status, size = 'md' }) {
  const statusMap = {
    active: 'status-active',
    running: 'status-running',
    pending: 'status-pending',
    error: 'status-error',
    disabled: 'status-pending',
    enabled: 'status-active',
    healthy: 'status-active',
    unhealthy: 'status-error',
  }
  const className = statusMap[status?.toLowerCase()] || 'status-active'
  return (
    <span className={`status ${className}`}>
      <span className="status-dot" />
      {status}
    </span>
  )
}

// Form Input
export function Input({ label, error, ...props }) {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <input className={`form-input ${error ? 'error' : ''}`} {...props} />
      {error && <span className="form-error">{error}</span>}
    </div>
  )
}

// Form Select
export function Select({ label, options, error, ...props }) {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <select className={`form-input ${error ? 'error' : ''}`} {...props}>
        {options.map(opt => (
          <option key={opt.value || opt} value={opt.value || opt}>
            {opt.label || opt}
          </option>
        ))}
      </select>
      {error && <span className="form-error">{error}</span>}
    </div>
  )
}

// Form Textarea
export function Textarea({ label, error, ...props }) {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <textarea className={`form-input ${error ? 'error' : ''}`} {...props} />
      {error && <span className="form-error">{error}</span>}
    </div>
  )
}

// Loading Spinner
export function Spinner({ size = 24 }) {
  return (
    <div className="spinner-container">
      <div className="spinner" style={{ width: size, height: size }} />
    </div>
  )
}

// Empty State
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="empty-state">
      {Icon && <Icon size={48} />}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  )
}

// Alert/Toast
export function Alert({ type = 'info', title, message, onClose }) {
  const icons = { info: Info, success: CheckCircle, warning: AlertTriangle, error: AlertCircle }
  const Icon = icons[type]
  return (
    <div className={`alert alert-${type}`}>
      <Icon size={20} />
      <div className="alert-content">
        {title && <div className="alert-title">{title}</div>}
        <div className="alert-message">{message}</div>
      </div>
      {onClose && <button className="alert-close" onClick={onClose}><X size={16} /></button>}
    </div>
  )
}

// Table Component
export function Table({ columns, data, loading, emptyMessage = 'No data found', onRowClick }) {
  if (loading) return <div className="table-loading"><Spinner /></div>
  if (!data?.length) return <EmptyState title={emptyMessage} />
  
  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>{columns.map((col, i) => <th key={i}>{col.header}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.id || i} onClick={() => onRowClick?.(row)} className={onRowClick ? 'clickable' : ''}>
              {columns.map((col, j) => (
                <td key={j}>{col.render ? col.render(row) : row[col.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Stats Card
export function StatCard({ icon: Icon, label, value, change, trend, color = 'blue' }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}><Icon size={20} /></div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {change && (
        <div className={`stat-change ${trend === 'up' ? 'positive' : trend === 'down' ? 'negative' : ''}`}>
          {change}
        </div>
      )}
    </div>
  )
}

// Resource Icon
export function ResourceIcon({ type, size = 14 }) {
  return <div className={`resource-icon ${type}`}><span>{type?.[0]?.toUpperCase()}</span></div>
}

// Confirm Dialog
export function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmText = 'Confirm', loading }) {
  return (
    <Modal open={open} onClose={onClose} title={title} footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button variant="danger" onClick={onConfirm} loading={loading}>{confirmText}</Button>
      </>
    }>
      <p>{message}</p>
    </Modal>
  )
}

// Tabs
export function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div className="tabs">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.icon && <tab.icon size={16} />}
          {tab.label}
        </button>
      ))}
    </div>
  )
}

// Code Block
export function CodeBlock({ code, language = 'json' }) {
  const formatted = typeof code === 'object' ? JSON.stringify(code, null, 2) : code
  return <pre className="code-block"><code>{formatted}</code></pre>
}
